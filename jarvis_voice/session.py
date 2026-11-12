import json
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Protocol


class Recognizer(Protocol):
    def AcceptWaveform(self, data: bytes) -> bool: ...
    def Result(self) -> str: ...
    def PartialResult(self) -> str: ...
    def Reset(self) -> None: ...


class SessionState(Enum):
    IDLE = auto()
    LISTENING = auto()
    STOPPED = auto()


@dataclass(frozen=True)
class SessionConfig:
    wake_word: str = "джарвис"
    end_word: str = "конец"
    shutdown_phrase: str = "пока джарвис"
    # Распознаватель wake word работает по маленькой грамматике и на промежуточных результатах
    # склонен «подгонять» любую речь под «джарвис». Поэтому запись включается только по
    # окончательному результату, с достаточной уверенностью и не сразу после «конец».
    wake_on_partial: bool = False
    min_wake_confidence: float = 0.0
    wake_cooldown_chunks: int = 0


class VoiceSession:
    def __init__(
        self,
        wake_recognizer: Recognizer,
        speech_recognizer: Recognizer,
        on_listen: Callable[[], None],
        on_text: Callable[[str], None],
        on_shutdown: Callable[[], None],
        config: SessionConfig = SessionConfig(),
    ) -> None:
        self.wake_recognizer = wake_recognizer
        self.speech_recognizer = speech_recognizer
        self.on_listen = on_listen
        self.on_text = on_text
        self.on_shutdown = on_shutdown
        self.config = config
        self.state = SessionState.IDLE
        self.parts: list[str] = []
        self.last_partial = ""
        self.cooldown = 0

    def process(self, data: bytes) -> None:
        if self.state == SessionState.STOPPED:
            return
        if self.state == SessionState.IDLE:
            self._process_wake_word(data)
        else:
            self._process_speech(data)

    def _process_wake_word(self, data: bytes) -> None:
        if self.cooldown > 0:
            # Хвост фразы с «конец» и звук вставки не должны снова запускать запись.
            self.cooldown -= 1
            if self.cooldown == 0:
                self.wake_recognizer.Reset()
            return

        is_final = self.wake_recognizer.AcceptWaveform(data)
        if not is_final and not self.config.wake_on_partial:
            return
        payload = self.wake_recognizer.Result() if is_final else self.wake_recognizer.PartialResult()
        text = self._text_from_payload(payload, "text" if is_final else "partial")
        normalized = self._normalize(text)
        if self.config.shutdown_phrase in normalized:
            self._shutdown()
            return
        if self.config.wake_word not in normalized.split():
            return
        if is_final and self._wake_confidence(payload) < self.config.min_wake_confidence:
            return

        self.state = SessionState.LISTENING
        self.parts = []
        self.last_partial = ""
        self.wake_recognizer.Reset()
        self.speech_recognizer.Reset()
        self.on_listen()

    def _process_speech(self, data: bytes) -> None:
        is_final = self.speech_recognizer.AcceptWaveform(data)
        payload = self.speech_recognizer.Result() if is_final else self.speech_recognizer.PartialResult()
        text = self._text_from_payload(payload, "text" if is_final else "partial")
        normalized = self._normalize(text)

        if self.config.shutdown_phrase in normalized:
            self._shutdown()
            return

        if self.config.end_word in normalized.split():
            prefix = self._before_end_word(text)
            if is_final:
                if prefix:
                    self.parts.append(prefix)
                self.last_partial = ""
            else:
                self.last_partial = prefix
            self._finish()
            return

        if is_final:
            if text:
                self.parts.append(text)
            self.last_partial = ""
        else:
            self.last_partial = text

    def _finish(self) -> None:
        parts = [*self.parts]
        if self.last_partial:
            parts.append(self.last_partial)
        text = " ".join(parts).strip()
        self._reset()
        self.cooldown = self.config.wake_cooldown_chunks
        if text:
            self.on_text(text)

    def _shutdown(self) -> None:
        self._reset()
        self.state = SessionState.STOPPED
        self.on_shutdown()

    def _reset(self) -> None:
        self.state = SessionState.IDLE
        self.parts = []
        self.last_partial = ""
        self.wake_recognizer.Reset()
        self.speech_recognizer.Reset()

    def _before_end_word(self, text: str) -> str:
        normalized = self._normalize(text)
        end_index = normalized.split().index(self.config.end_word)
        return " ".join(text.split()[:end_index]).strip()

    def _wake_confidence(self, payload: str) -> float:
        """Уверенность распознавания wake word; 1.0, если распознаватель не вернул слова."""
        try:
            words = json.loads(payload).get("result")
        except (json.JSONDecodeError, AttributeError):
            return 1.0
        if not isinstance(words, list) or not words:
            return 1.0
        scores = [
            float(item.get("conf", 1.0))
            for item in words
            if isinstance(item, dict) and self._normalize(str(item.get("word", ""))) == self.config.wake_word
        ]
        return max(scores) if scores else 0.0

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().replace("ё", "е").split())

    @staticmethod
    def _text_from_payload(payload: str, key: str) -> str:
        try:
            value = json.loads(payload).get(key, "")
            return value.strip() if isinstance(value, str) else ""
        except (json.JSONDecodeError, AttributeError):
            return ""
