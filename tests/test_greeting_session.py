import unittest
from unittest.mock import call, patch

from jarvis_voice import app


class GreetingSessionTest(unittest.TestCase):
    @patch("jarvis_voice.app.speak_text")
    def test_full_greeting_is_used_only_once_per_run(self, speak_text):
        previous = app.greeted
        app.greeted = False
        try:
            app.on_listen()
            app.on_listen()
            app.on_listen()
        finally:
            app.greeted = previous

        self.assertEqual(
            speak_text.call_args_list,
            [call(app.GREETING), call("Слушаю"), call("Слушаю")],
        )


if __name__ == "__main__":
    unittest.main()
