import json
import os
import queue
import sys
from pathlib import Path

import sounddevice as sd
from vosk import KaldiRecognizer, Model, SetLogLevel

from jarvis_voice.platform_io import insert_text, play_beep, speak_greeting
from jarvis_voice.session import SessionConfig, VoiceSession

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "vosk-model-small-ru-0.22"
SAMPLE_RATE = 16000
GREETING = os.environ.get("JARVIS_GREETING", "Здравствуйте, Сын Пелея")


class ShutdownRequested(Exception):
    pass


def on_listen() -> None:
    try:
        speak_greeting(GREETING)
    except Exception as error:
        print(f"Не удалось озвучить приветствие: {error}", file=sys.stderr, flush=True)
        play_beep()
    print("Слушаю...", flush=True)


def on_text(text: str) -> None:
    print(f"Распознано: {text}", flush=True)
    try:
        insert_text(text)
    except PermissionError as error:
        print(str(error), file=sys.stderr, flush=True)


def shutdown() -> None:
    raise ShutdownRequested


def main() -> int:
    if not MODEL_PATH.exists():
        print("Модель не найдена. Запустите ./setup.sh", file=sys.stderr)
        return 1

    SetLogLevel(-1)
    model = Model(str(MODEL_PATH))
    wake_grammar = json.dumps(["джарвис", "пока джарвис", "[unk]"], ensure_ascii=False)
    wake_recognizer = KaldiRecognizer(model, SAMPLE_RATE, wake_grammar)
    speech_recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    audio_queue: queue.Queue[bytes] = queue.Queue()

    def handle_listen() -> None:
        on_listen()
        while True:
            try:
                audio_queue.get_nowait()
            except queue.Empty:
                break
        speech_recognizer.Reset()

    session = VoiceSession(
        wake_recognizer,
        speech_recognizer,
        on_listen=handle_listen,
        on_text=on_text,
        on_shutdown=shutdown,
        config=SessionConfig(),
    )

    def audio_callback(indata, frames, time_info, status) -> None:
        if status:
            print(status, file=sys.stderr, flush=True)
        audio_queue.put(bytes(indata))

    print("Готов. «Джарвис» — начать, «конец» — вставить текст.", flush=True)
    print("Остановка: «пока Джарвис» или Ctrl+C.", flush=True)
    try:
        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=4000,
            dtype="int16",
            channels=1,
            callback=audio_callback,
        ):
            while True:
                session.process(audio_queue.get())
    except (KeyboardInterrupt, ShutdownRequested):
        print("\nОстановлено.")
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        print("Проверьте микрофон, буфер обмена и разрешения для вставки текста.", file=sys.stderr)
        return 1
    return 0
