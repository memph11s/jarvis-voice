import importlib.util
import os
import sys
import tempfile
import warnings
import wave
from pathlib import Path

from jarvis_voice.piper_tts import play_wav

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "silero" / "v5_6_ru.pt"
SAMPLE_RATE = 48000
_model = None


def models_available() -> bool:
    return MODEL_PATH.is_file() and importlib.util.find_spec("torch") is not None


def _load_model():
    global _model
    if _model is None:
        import torch

        torch.set_num_threads(4)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            _model = torch.package.PackageImporter(str(MODEL_PATH)).load_pickle("tts_models", "model")
    return _model


def speak(text: str) -> bool:
    if not models_available():
        return False

    try:
        model = _load_model()
        audio = model.apply_tts(
            text=text,
            sample_rate=SAMPLE_RATE,
            speaker=os.environ.get("JARVIS_SILERO_SPEAKER", "eugene"),
        )
        samples = (audio.numpy() * 32767).astype("int16")
        with tempfile.TemporaryDirectory(prefix="jarvis-tts-") as directory:
            output = Path(directory) / "speech.wav"
            with wave.open(str(output), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(SAMPLE_RATE)
                wav.writeframes(samples.tobytes())
            return play_wav(output)
    except Exception as error:
        print(f"Silero speech failed: {error}", file=sys.stderr)
        return False
