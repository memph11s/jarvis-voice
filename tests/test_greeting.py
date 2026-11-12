import base64
import unittest
from unittest.mock import Mock, patch

from jarvis_voice.platform_io import speak_greeting


class GreetingTest(unittest.TestCase):
    @patch("jarvis_voice.platform_io.subprocess.run")
    @patch("jarvis_voice.platform_io.platform.system", return_value="Darwin")
    def test_macos_uses_russian_voice(self, system, run):
        run.return_value = Mock(returncode=0)

        speak_greeting("Привет, Никита")

        run.assert_called_once_with(["say", "-v", "Lesya", "Привет, Никита"], check=False)

    @patch("jarvis_voice.platform_io.subprocess.run")
    @patch("jarvis_voice.platform_io.platform.system", return_value="Windows")
    def test_windows_uses_system_speech(self, system, run):
        speak_greeting("Привет, Никита")

        args, kwargs = run.call_args
        self.assertEqual(args[0][:3], ["powershell", "-NoProfile", "-Command"])
        self.assertIn("System.Speech", args[0][3])
        self.assertEqual(
            base64.b64decode(kwargs["input"]).decode("utf-16le"),
            "Привет, Никита",
        )

    @patch("jarvis_voice.platform_io.subprocess.run")
    @patch("jarvis_voice.platform_io.shutil.which", return_value="/usr/bin/spd-say")
    @patch("jarvis_voice.platform_io.platform.system", return_value="Linux")
    def test_linux_uses_speech_dispatcher(self, system, which, run):
        speak_greeting("Привет, Никита")

        run.assert_called_once_with(["spd-say", "--wait", "Привет, Никита"], check=False)
    @patch("jarvis_voice.platform_io.speak_greeting")
    @patch("jarvis_voice.piper_tts.speak", return_value=True)
    def test_piper_is_preferred_for_speech(self, piper, system_speech):
        from jarvis_voice.platform_io import speak_text

        speak_text("Привет")

        piper.assert_called_once_with("Привет")
        system_speech.assert_not_called()

    @patch("jarvis_voice.platform_io.speak_greeting")
    @patch("jarvis_voice.piper_tts.speak", return_value=False)
    def test_system_voice_is_fallback_when_piper_is_unavailable(self, piper, system_speech):
        from jarvis_voice.platform_io import speak_text

        speak_text("Привет")

        system_speech.assert_called_once_with("Привет")


if __name__ == "__main__":
    unittest.main()
