import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from jarvis_voice import app


class AppPrivacyTest(unittest.TestCase):
    def setUp(self):
        self.private_mode = app.PRIVATE_MODE
        app.PRIVATE_MODE = True

    def tearDown(self):
        app.PRIVATE_MODE = self.private_mode

    @patch("jarvis_voice.app.insert_text")
    def test_regular_dictation_is_pasted_with_punctuation(self, insert_text):
        app.on_text("проверь этот тест")

        insert_text.assert_called_once_with("Проверь этот тест.")

    @patch("jarvis_voice.app.insert_text")
    def test_private_mode_does_not_log_recognized_text(self, insert_text):
        output = io.StringIO()
        with redirect_stdout(output):
            app.on_text("секретная фраза")

        self.assertNotIn("секретная фраза", output.getvalue())
        self.assertIn("Текст распознан", output.getvalue())

    @patch("jarvis_voice.app.speak_text")
    @patch("jarvis_voice.app.insert_text")
    @patch("jarvis_voice.app.ollama.ask", return_value="Локальный ответ")
    def test_question_uses_only_local_ollama(self, ask, insert_text, speak_text):
        app.on_text("спроси почему небо голубое")

        ask.assert_called_once_with("почему небо голубое")
        speak_text.assert_called_once_with("Локальный ответ")
        insert_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()
