import json
from urllib.request import Request, urlopen


class OllamaClient:
    def __init__(
        self,
        model: str = "qwen3:4b",
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 120.0,
    ) -> None:
        if base_url not in {"http://127.0.0.1:11434", "http://localhost:11434"}:
            raise ValueError("Ollama endpoint must be local")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def ask(self, question: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты Джарвис, локальный голосовой помощник. Отвечай по-русски, "
                        "кратко и по делу. Не утверждай, что выполнил действия на компьютере."
                    ),
                },
                {"role": "user", "content": question},
            ],
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        answer = result.get("message", {}).get("content", "").strip()
        if not answer:
            raise RuntimeError("Ollama returned an empty answer")
        return answer
