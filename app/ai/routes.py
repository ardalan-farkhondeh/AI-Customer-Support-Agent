
import logging
import os
import secrets
import re

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    status,
    Depends,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.llm import generate_response
from app.retrieval.retriever import retrieve_context
from app.database.dependencies import get_db
from app.database.models import Customer
from app.tools.order_lookup import get_order_status

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    telegram_id: int = Field(gt=0)


class AskResponse(BaseModel):
    answer: str


def is_greeting(question: str) -> bool:
    text = re.sub(
        r"[^\w\s]",
        "",
        question.lower()
    ).strip()

    greetings = {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "howdy",
        "سلام",
        "درود",
        "صبح بخیر",
    }

    return text in greetings


# =========================
# Tool Definition
# =========================

ORDER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": (
                "Get the status of an order belonging "
                "to the current customer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The order ID."
                    }
                },
                "required": ["order_id"]
            }
        }
    }
]


@router.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
)
async def ask_ai(
    request: AskRequest,
    x_internal_api_key: str = Header(
        ...,
        alias="x-internal-api-key",
    ),
    db: Session = Depends(get_db),
):

    expected_key = os.getenv("INTERNAL_API_KEY", "")

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured.",
        )

    if not secrets.compare_digest(
        x_internal_api_key,
        expected_key,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty.",
        )

    try:

        # Greeting: no RAG or tools.
        if is_greeting(question):
            return AskResponse(
                answer=(
                    "Hello! Welcome to our support service. "
                    "How can I help you today?"
                )
            )

        # Retrieve relevant knowledge.
        retrieval_result = retrieve_context(
            question,
            n_results=3,
        )

        context = retrieval_result.get("context", "")

        # Identify the authenticated customer.
        customer = db.execute(
            select(Customer).where(
                Customer.telegram_id == request.telegram_id
            )
        ).scalar_one_or_none()

        # Tool handler uses the customer ID from the database.
        def order_status_handler(order_id: int):

            if not isinstance(order_id, int) or isinstance(order_id, bool):
                raise ValueError("Invalid order ID.")

            if order_id <= 0:
                raise ValueError("Invalid order ID.")

            if customer is None:
                return {
                    "success": False,
                    "message": "Customer account not found."
                }

            return get_order_status(
                db=db,
                order_id=order_id,
                customer_id=customer.id,
            )

        tool_handlers = {
            "get_order_status": order_status_handler
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a customer support assistant. "
                    "Answer using the knowledge base context. "
                    "Do not invent information. "
                    "If the context does not contain the answer, "
                    "say that you do not have that information. "
                    "If the customer explicitly asks about an "
                    "order status or tracking, use the "
                    "get_order_status tool. "
                    "Never invent order information. "
                    "Use the tool result as the source of truth. "
                    "If the order is not found, explain that "
                    "you could not find the order. "
                    "Keep answers clear and concise."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Knowledge base context:\n"
                    f"{context or 'No relevant context found.'}\n\n"
                    f"Customer question:\n{question}"
                ),
            },
        ]

        answer = await generate_response(
            messages=messages,
            tools=ORDER_TOOLS,
            tool_handlers=tool_handlers,
        )

        if not answer or not answer.strip():
            raise RuntimeError("AI returned an empty response.")

        return AskResponse(answer=answer.strip())

    except RuntimeError as exc:
        logger.error("AI processing failed: %s", exc)

        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable.",
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected AI endpoint error.")

        raise HTTPException(
            status_code=500,
            detail="AI processing failed.",
        ) from exc
