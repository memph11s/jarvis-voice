import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "piper" / "ru_RU-dmitri-medium.onnx"
CONFIG_PATH = ROOT / "models" / "piper" / "ru_RU-dmitri-medium.onnx.json"


def models_available() -> bool:
    return MODEL_PATH.is_file() and CONFIG_PATH.is_file()


def speak(text: str) -> bool:
    if not models_available():
        return False

    with tempfile.TemporaryDirectory(prefix="jarvis-tts-") as directory:
        output = Path(directory) / "speech.wav"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "piper",
                "-m",
                str(MODEL_PATH),
                "-c",
                str(CONFIG_PATH),
                "-f",
                str(output),
            ],
            input=text,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0 or not output.is_file():
            return False
        return _play_wav(output)


def _play_wav(path: Path) -> bool:
    system = platform.system()
    if system == "Darwin":
        command = ["afplay", str(path)]
    elif system == "Windows":
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            "(New-Object Media.SoundPlayer $args[0]).PlaySync()",
            str(path),
        ]
    elif system == "Linux":
        command = ["paplay", str(path)]
    else:
        return False

    try:
        return subprocess.run(command, check=False).returncode == 0
    except FileNotFoundError:
        if system == "Linux":
            return subprocess.run(["aplay", str(path)], check=False).returncode == 0
        return False
