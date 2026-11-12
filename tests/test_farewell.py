import unittest
from unittest.mock import patch

from jarvis_voice import app


class FarewellTest(unittest.TestCase):
    @patch("jarvis_voice.app.speak_text")
    def test_shutdown_speaks_farewell_before_stopping(self, speak_text):
        with self.assertRaises(app.ShutdownRequested):
            app.shutdown()

        speak_text.assert_called_once_with("Хороших выходных, Сэр")

    @patch("jarvis_voice.app.speak_text", side_effect=RuntimeError("speech unavailable"))
    def test_shutdown_still_stops_when_speech_fails(self, speak_text):
        with self.assertRaises(app.ShutdownRequested):
            app.shutdown()


if __name__ == "__main__":
    unittest.main()
