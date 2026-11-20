
import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:3b"


def test_ollama():
    print("Testing Ollama connection...")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Reply with OK"
            }
        ],
        "stream": False
    }

    try:
        response = httpx.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        print("\nOllama response:")
        print(result["message"]["content"])

        print("\nOllama connection successful!")

    except Exception as e:
        print("\nOllama connection failed:")
        print(e)


if __name__ == "__main__":
    test_ollama()
