
import os
import logging
import httpx

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# Configuration
# =========================

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

API_URL = "http://127.0.0.1:8000/telegram/events"
AI_API_URL = "http://127.0.0.1:8000/ai/ask"

HTTP_TIMEOUT = 15.0
AI_TIMEOUT = 130.0


# =========================
# HTTP Client
# =========================

async def save_telegram_event(
    user,
    chat_id,
    message_id,
    direction,
    message_text
):
    payload = {
        "telegram_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "chat_id": chat_id,
        "telegram_message_id": message_id,
        "direction": direction,
        "message": message_text
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(
            API_URL,
            json=payload
        )
        response.raise_for_status()
        return response.json()


# =========================
# Ask AI Agent
# =========================

async def ask_ai(question, telegram_id):

    if not INTERNAL_API_KEY:
        raise RuntimeError("INTERNAL_API_KEY is not configured")

    payload = {
        "question": question,
        "telegram_id": telegram_id
    }

    headers = {
        "x-internal-api-key": INTERNAL_API_KEY
    }

    logger.info(
        "Sending message to AI. Telegram ID: %s",
        telegram_id
    )

    async with httpx.AsyncClient(timeout=AI_TIMEOUT) as client:
        response = await client.post(
            AI_API_URL,
            json=payload,
            headers=headers
        )

        response.raise_for_status()

        data = response.json()
        answer = data.get("answer")

        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("AI API returned an empty response")

        return answer.strip()


# =========================
# Send and Save Response
# =========================

async def send_response(update, response):

    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or not chat:
        return

    try:
        sent_message = await message.reply_text(response)

        try:
            await save_telegram_event(
                user,
                chat.id,
                sent_message.message_id,
                "outgoing",
                response
            )

        except Exception:
            logger.exception("Failed to save outgoing Telegram message")

    except Exception:
        logger.exception("Failed to send Telegram response")


# =========================
# Start Command
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    message = update.effective_message
    chat = update.effective_chat

    if not user or not message or not chat:
        return

    try:
        await save_telegram_event(
            user,
            chat.id,
            message.message_id,
            "incoming",
            message.text or "/start"
        )

    except Exception:
        logger.exception("Failed to save start message")

    await send_response(
        update,
        "Hello! Welcome to SupportPilot AI. How can I help you?"
    )


# =========================
# Handle Customer Messages
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    message = update.effective_message
    chat = update.effective_chat

    if not user or not message or not chat:
        return

    user_message = (message.text or "").strip()

    if not user_message:
        return

    logger.info("Received message from Telegram ID: %s", user.id)

    # Save incoming message
    try:
        await save_telegram_event(
            user,
            chat.id,
            message.message_id,
            "incoming",
            user_message
        )

    except Exception:
        logger.exception("Failed to save incoming message")

    # Generate AI response
    try:
        response = await ask_ai(
            user_message,
            user.id
        )

    except httpx.TimeoutException:
        logger.exception("AI request timed out")
        response = (
            "Sorry, the AI service is taking too long "
            "to respond. Please try again."
        )

    except httpx.HTTPStatusError as error:
        logger.error(
            "AI API error. Status: %s, Response: %s",
            error.response.status_code,
            error.response.text
        )
        response = (
            "Sorry, I'm having trouble processing "
            "your question right now."
        )

    except Exception:
        logger.exception("AI response generation failed")
        response = (
            "Sorry, the AI service is temporarily "
            "unavailable. Please try again later."
        )

    await send_response(update, response)


# =========================
# Error Handler
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.error(
        "Exception while handling Telegram update",
        exc_info=context.error
    )


# =========================
# Main
# =========================

def main():

    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")

    if not INTERNAL_API_KEY:
        raise ValueError("INTERNAL_API_KEY not found in .env")

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    application.add_error_handler(error_handler)

    logger.info("SupportPilot AI Telegram bot is starting...")

    application.run_polling()


if __name__ == "__main__":
    main()
