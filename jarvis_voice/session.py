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

    def process(self, data: bytes) -> None:
        if self.state == SessionState.STOPPED:
            return
        if self.state == SessionState.IDLE:
            self._process_wake_word(data)
        else:
            self._process_speech(data)

    def _process_wake_word(self, data: bytes) -> None:
        is_final = self.wake_recognizer.AcceptWaveform(data)
        payload = self.wake_recognizer.Result() if is_final else self.wake_recognizer.PartialResult()
        text = self._text_from_payload(payload, "text" if is_final else "partial")
        normalized = self._normalize(text)
        if self.config.shutdown_phrase in normalized:
            self._shutdown()
            return
        if self.config.wake_word not in normalized.split():
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
