
import inspect
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434",
).rstrip("/")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b",
)


async def generate_response(
    messages: list,
    tools: list | None = None,
    tool_handlers: dict | None = None,
    max_tool_rounds: int = 2,
) -> str:

    if not isinstance(messages, list) or not messages:
        raise ValueError("Messages must be a non-empty list.")

    if max_tool_rounds < 0:
        raise ValueError("Invalid maximum tool rounds.")

    conversation = [
        dict(message)
        for message in messages
    ]

    handlers = tool_handlers or {}

    async with httpx.AsyncClient(timeout=120.0) as client:

        for round_index in range(max_tool_rounds + 1):

            payload = {
                "model": OLLAMA_MODEL,
                "messages": conversation,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                },
            }

            if tools:
                payload["tools"] = tools

            try:
                response = await client.post(
                    f"{OLLAMA_URL}/api/chat",
                    json=payload,
                )

                response.raise_for_status()
                data = response.json()

            except (httpx.HTTPError, ValueError) as exc:
                raise RuntimeError(
                    "Ollama request failed."
                ) from exc

            message = data.get("message") or {}

            if not isinstance(message, dict):
                raise RuntimeError("Invalid Ollama response.")

            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                answer = (message.get("content") or "").strip()

                if not answer:
                    raise RuntimeError(
                        "Ollama returned an empty response."
                    )

                return answer

            if round_index >= max_tool_rounds:
                raise RuntimeError(
                    "Maximum tool-calling rounds exceeded."
                )

            conversation.append(message)

            for call in tool_calls:

                function = call.get("function") or {}
                tool_name = function.get("name")
                arguments = function.get("arguments") or {}

                handler = handlers.get(tool_name)

                try:
                    if handler is None:
                        raise ValueError("Unsupported tool.")

                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)

                    if not isinstance(arguments, dict):
                        raise ValueError("Invalid tool arguments.")

                    result = handler(**arguments)

                    if inspect.isawaitable(result):
                        result = await result

                    tool_result = {
                        "success": True,
                        "result": result,
                    }

                except Exception:
                    tool_result = {
                        "success": False,
                        "error": "Tool execution failed.",
                    }

                conversation.append({
                    "role": "tool",
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                        default=str,
                    ),
                })

    raise RuntimeError(
        "Unable to complete the Ollama conversation."
    )
