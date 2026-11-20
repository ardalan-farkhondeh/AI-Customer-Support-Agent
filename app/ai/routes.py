
import logging
import os
import secrets
import re

from dotenv import load_dotenv
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.ai.llm import generate_response
from app.retrieval.retriever import retrieve_context

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

        # Greeting: no RAG, no tools, no customer lookup.
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

        if not context or not context.strip():
            return AskResponse(
                answer=(
                    "I'm sorry, I couldn't find this information "
                    "in our knowledge base. Please contact our "
                    "support team for assistance."
                )
            )

        # Answer using retrieved knowledge only.
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a customer support assistant. "
                    "Answer using ONLY the knowledge base context. "
                    "Do not invent information. "
                    "If the context does not contain the answer, "
                    "say that you do not have that information. "
                    "Answer the exact question asked. "
                    "Do not confuse shipping time with refund time. "
                    "Do not mention customer accounts or tracking "
                    "unless the question explicitly asks about them. "
                    "Keep answers clear and concise."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Knowledge base context:\n{context}\n\n"
                    f"Customer question:\n{question}"
                ),
            },
        ]

        answer = await generate_response(
            messages=messages,
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
