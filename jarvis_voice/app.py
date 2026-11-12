import json
import os
import queue
import sys
from pathlib import Path

import sounddevice as sd
from vosk import KaldiRecognizer, Model, SetLogLevel

from jarvis_voice.ollama_client import OllamaClient
from jarvis_voice.platform_io import insert_text, play_beep, speak_text
from jarvis_voice.session import SessionConfig, VoiceSession
from jarvis_voice.text_processing import extract_local_question, punctuate_text

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "vosk-model-small-ru-0.22"
SAMPLE_RATE = 16000
GREETING = os.environ.get("JARVIS_GREETING", "Здравствуйте, Сын Пелея")
PRIVATE_MODE = os.environ.get("JARVIS_PRIVATE_MODE", "true").lower() not in {"0", "false", "no"}
OLLAMA_MODEL = os.environ.get("JARVIS_OLLAMA_MODEL", "qwen2.5-coder:7b")
ollama = OllamaClient(model=OLLAMA_MODEL)


class ShutdownRequested(Exception):
    pass


def on_listen() -> None:
    try:
        speak_text(GREETING)
    except Exception as error:
        print(f"Не удалось озвучить приветствие: {error}", file=sys.stderr, flush=True)
        play_beep()
    print("Слушаю...", flush=True)


def on_text(text: str) -> None:
    question = extract_local_question(text)
    if question is not None:
        answer_question(question)
        return

    text = punctuate_text(text)
    print("Текст распознан" if PRIVATE_MODE else f"Распознано: {text}", flush=True)
    try:
        insert_text(text)
    except PermissionError as error:
        print(str(error), file=sys.stderr, flush=True)


def answer_question(question: str) -> None:
    if not question:
        speak_text("Что ты хочешь спросить?")
        return

    print("Запрос к локальной модели", flush=True)
    if not PRIVATE_MODE:
        print(f"Вопрос: {question}", flush=True)
    try:
        answer = ollama.ask(question)
    except Exception as error:
        print(f"Локальная модель недоступна: {error}", file=sys.stderr, flush=True)
        speak_text("Локальная модель недоступна")
        return

    print("Ответ получен" if PRIVATE_MODE else f"Ответ: {answer}", flush=True)
    speak_text(answer)


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

    def handle_text(text: str) -> None:
        on_text(text)
        while True:
            try:
                audio_queue.get_nowait()
            except queue.Empty:
                break
        wake_recognizer.Reset()
        speech_recognizer.Reset()

    session = VoiceSession(
        wake_recognizer,
        speech_recognizer,
        on_listen=handle_listen,
        on_text=handle_text,
        on_shutdown=shutdown,
        config=SessionConfig(),
    )

    def audio_callback(indata, frames, time_info, status) -> None:
        if status:
            print(status, file=sys.stderr, flush=True)
        audio_queue.put(bytes(indata))

    print("Готов. «Джарвис» — начать, «конец» — вставить текст.", flush=True)
    print("«Спроси …» — вопрос к локальной Ollama.", flush=True)
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
