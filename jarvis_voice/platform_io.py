import base64
import os
import platform
import shutil
import subprocess
from pathlib import Path

import pyperclip

BEEP_PATH = Path("/System/Library/Sounds/Glass.aiff")
LINUX_BEEP_PATH = Path("/usr/share/sounds/freedesktop/stereo/bell.oga")


def play_beep() -> None:
    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(
            ["afplay", str(BEEP_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    elif system == "Windows":
        import winsound

        winsound.Beep(880, 250)
    elif system == "Linux":
        if LINUX_BEEP_PATH.exists() and shutil.which("paplay"):
            subprocess.Popen(
                ["paplay", str(LINUX_BEEP_PATH)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            print("\a", end="", flush=True)
    else:
        print("\a", end="", flush=True)


def speak_greeting(text: str) -> None:
    system = platform.system()
    if system == "Darwin":
        voice = os.environ.get("JARVIS_VOICE", "Lesya")
        result = subprocess.run(["say", "-v", voice, text], check=False)
        if result.returncode != 0:
            subprocess.run(["say", text], check=False)
        return

    if system == "Windows":
        encoded = base64.b64encode(text.encode("utf-16le")).decode("ascii")
        script = (
            "$text=[Text.Encoding]::Unicode.GetString("
            "[Convert]::FromBase64String([Console]::In.ReadToEnd())); "
            "Add-Type -AssemblyName System.Speech; "
            "$speaker=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$speaker.Speak($text)"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            input=encoded,
            text=True,
            check=True,
        )
        return

    if system == "Linux":
        if shutil.which("spd-say"):
            subprocess.run(["spd-say", "--wait", text], check=False)
        elif shutil.which("espeak"):
            subprocess.run(["espeak", "-v", "ru", text], check=False)
        else:
            play_beep()
        return

    play_beep()


def macos_accessibility_enabled() -> bool:
    result = subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to get UI elements enabled'],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() == "true"


def insert_text(text: str) -> None:
    system = platform.system()
    if system == "Darwin" and not macos_accessibility_enabled():
        raise PermissionError(
            "Нет разрешения Accessibility для вставки. Включите Terminal, iTerm или VS Code "
            "в System Settings → Privacy & Security → Accessibility и перезапустите Jarvis."
        )

    pyperclip.copy(text)
    if system == "Darwin":
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to key code 9 using command down'],
            check=True,
        )
    elif system == "Windows":
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait("^v")',
            ],
            check=True,
        )
    elif system == "Linux":
        if os.environ.get("WAYLAND_DISPLAY"):
            subprocess.run(
                ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"],
                check=True,
            )
        else:
            subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"], check=True)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
