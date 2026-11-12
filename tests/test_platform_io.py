import unittest
from unittest.mock import patch

from jarvis_voice.platform_io import insert_text


class PlatformIoTest(unittest.TestCase):
    @patch("jarvis_voice.platform_io.macos_accessibility_enabled", return_value=True)
    @patch("jarvis_voice.platform_io.subprocess.run")
    @patch("jarvis_voice.platform_io.pyperclip.copy")
    @patch("jarvis_voice.platform_io.platform.system", return_value="Darwin")
    def test_paste_uses_active_window_without_opening_an_application(
        self,
        system,
        copy,
        run,
        accessibility,
    ):
        insert_text("текст")

        copy.assert_called_once_with("текст")
        run.assert_called_once_with(
            ["osascript", "-e", 'tell application "System Events" to key code 9 using command down'],
            check=True,
        )

    @patch("jarvis_voice.platform_io.pyperclip.copy")
    @patch("jarvis_voice.platform_io.macos_accessibility_enabled", return_value=False)
    @patch("jarvis_voice.platform_io.platform.system", return_value="Darwin")
    def test_missing_accessibility_permission_is_reported(self, system, accessibility, copy):
        with self.assertRaises(PermissionError):
            insert_text("текст")

        copy.assert_not_called()


if __name__ == "__main__":
    unittest.main()
