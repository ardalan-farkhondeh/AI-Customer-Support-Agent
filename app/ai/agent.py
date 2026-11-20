
import logging
import os
import re

import httpx
from dotenv import load_dotenv

from app.ai.llm import generate_response
from app.ai.prompts import build_messages

load_dotenv()

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": (
                "Look up a specific personal order. "
                "Use ONLY when the customer explicitly asks "
                "about their own order status or delivery."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tracking_number": {
                        "type": "string",
                    }
                },
                "required": ["tracking_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_customer",
            "description": (
                "Retrieve the customer's personal account "
                "information. Use ONLY when explicitly asked "
                "about their own account."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


def _is_greeting(question: str) -> bool:
    text = question.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)

    greetings = {
        "hi", "hello", "hey",
        "good morning", "good afternoon",
        "good evening", "howdy",
        "سلام", "درود", "صبح بخیر",
    }

    return text in greetings


def _needs_personal_tool(question: str) -> bool:
    text = question.lower()

    personal_keywords = (
        "my order",
        "my tracking",
        "my shipment",
        "my delivery",
        "where is my order",
        "track my order",
        "order status",
        "my account",
        "my profile",
        "my personal information",
        "سفارش من",
        "پیگیری سفارش",
        "وضعیت سفارش",
        "حساب کاربری من",
    )

    return any(keyword in text for keyword in personal_keywords)


async def _api_request(method: str, path: str, **kwargs):

    if not INTERNAL_API_KEY:
        raise RuntimeError(
            "Internal API authentication is not configured."
        )

    headers = dict(kwargs.pop("headers", {}))
    headers["x-internal-api-key"] = INTERNAL_API_KEY

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(
                method,
                f"{API_BASE_URL}{path}",
                headers=headers,
                **kwargs,
            )

            response.raise_for_status()
            return response.json()

    except (httpx.HTTPError, ValueError) as exc:
        logger.exception("Internal API request failed.")
        raise RuntimeError(
            "Internal API request failed."
        ) from exc


async def run_agent(
    question: str,
    context: str,
    telegram_id: int,
) -> str:

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    if (
        not isinstance(telegram_id, int)
        or isinstance(telegram_id, bool)
        or telegram_id <= 0
    ):
        raise ValueError("Invalid Telegram ID.")

    messages = build_messages(
        question=question,
        context=context,
        telegram_id=telegram_id,
    )

    # Greetings do not require tools or knowledge retrieval.
    if _is_greeting(question):
        return await generate_response(messages=messages)

    # General questions use RAG context directly.
    if not _needs_personal_tool(question):
        return await generate_response(messages=messages)

    async def lookup_order(tracking_number: str):

        if not isinstance(tracking_number, str):
            raise ValueError("Invalid tracking number.")

        tracking_number = tracking_number.strip()

        if not tracking_number or len(tracking_number) > 100:
            raise ValueError("Invalid tracking number.")

        return await _api_request(
            "POST",
            "/orders/lookup",
            json={
                "telegram_id": telegram_id,
                "tracking_number": tracking_number,
            },
        )

    async def lookup_customer():

        return await _api_request(
            "GET",
            "/customers/lookup",
            params={"telegram_id": telegram_id},
        )

    response = await generate_response(
        messages=messages,
        tools=TOOLS,
        tool_handlers={
            "lookup_order": lookup_order,
            "lookup_customer": lookup_customer,
        },
        max_tool_rounds=2,
    )

    if not isinstance(response, str) or not response.strip():
        raise RuntimeError("Agent returned an empty response.")

    return response.strip()
