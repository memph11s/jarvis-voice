import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from jarvis_voice.ollama_client import OllamaClient


class OllamaClientTest(unittest.TestCase):
    def test_request_stays_local_and_contains_only_current_question(self):
        response = Mock()
        response.read.return_value = json.dumps({
            "message": {"content": "Локальный ответ"},
        }).encode("utf-8")
        urlopen = MagicMock()
        urlopen.return_value.__enter__.return_value = response

        with patch("jarvis_voice.ollama_client.urlopen", urlopen):
            answer = OllamaClient(model="test-model").ask("Первый вопрос")

        self.assertEqual(answer, "Локальный ответ")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["messages"][-1], {"role": "user", "content": "Первый вопрос"})
        self.assertEqual(len(payload["messages"]), 2)

    def test_external_endpoint_is_rejected(self):
        with self.assertRaises(ValueError):
            OllamaClient(base_url="https://example.com")


if __name__ == "__main__":
    unittest.main()
