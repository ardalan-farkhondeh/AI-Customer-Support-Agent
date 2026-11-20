
import os
import secrets
import logging
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.dependencies import get_db
from app.database.models import Message, Customer, TelegramMessage, Order
from app.ai.routes import router as ai_router


# =========================
# Configuration
# =========================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Customer Support Agent",
    description="AI-powered customer support system",
    version="0.1.0"
)

app.include_router(ai_router)


# =========================
# Authentication
# =========================

def verify_internal_api_key(
    x_internal_api_key: str = Header(..., alias="x-internal-api-key")
):
    expected_key = os.getenv("INTERNAL_API_KEY")

    if not expected_key:
        logger.error("INTERNAL_API_KEY is not configured")
        raise HTTPException(
            status_code=500,
            detail="Internal API authentication is not configured"
        )

    if not secrets.compare_digest(x_internal_api_key, expected_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return True


# =========================
# Pydantic Schemas
# =========================

class OrderLookupRequest(BaseModel):
    telegram_id: int = Field(gt=0)
    tracking_number: str = Field(min_length=1, max_length=100)


class MessageCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    message: str = Field(min_length=4, max_length=1000)


class CustomerCreate(BaseModel):
    telegram_id: int | None = Field(default=None, gt=0)
    username: str | None = Field(default=None, max_length=100)
    full_name: str | None = Field(default=None, max_length=200)


class TelegramEventCreate(BaseModel):
    telegram_id: int = Field(gt=0)
    username: str | None = Field(default=None, max_length=100)
    full_name: str | None = Field(default=None, max_length=200)
    chat_id: int
    telegram_message_id: int = Field(gt=0)
    direction: Literal["incoming", "outgoing"]
    message: str = Field(min_length=1, max_length=10000)


# =========================
# Home
# =========================

@app.get("/")
def home():
    return {
        "message": "AI Customer Support Agent is running"
    }


# =========================
# Health Check
# =========================

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except SQLAlchemyError:
        logger.exception("Health check database failure")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )


# =========================
# Message CRUD
# =========================

@app.post("/messages", status_code=201)
def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    if message.message.strip().lower() == "test":
        raise HTTPException(
            status_code=400,
            detail="Test message is not allowed"
        )

    try:
        new_message = Message(**message.model_dump())
        db.add(new_message)
        db.commit()
        db.refresh(new_message)

        return {
            "status": "success",
            "message": {
                "id": new_message.id,
                "name": new_message.name,
                "email": new_message.email,
                "message": new_message.message
            }
        }

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to create message")
        raise HTTPException(
            status_code=500,
            detail="Failed to create message"
        )


@app.get("/messages")
def get_messages(db: Session = Depends(get_db)):
    messages = db.query(Message).order_by(Message.id).all()
    return {
        "total": len(messages),
        "messages": messages
    }


@app.get("/messages/{message_id}")
def get_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    message = db.get(Message, message_id)

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


@app.put("/messages/{message_id}")
def update_message(
    message_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    message = db.get(Message, message_id)

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    try:
        message.name = message_data.name
        message.email = str(message_data.email)
        message.message = message_data.message

        db.commit()
        db.refresh(message)

        return {
            "status": "success",
            "message": {
                "id": message.id,
                "name": message.name,
                "email": message.email,
                "message": message.message
            }
        }

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to update message")
        raise HTTPException(
            status_code=500,
            detail="Failed to update message"
        )


@app.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    message = db.get(Message, message_id)

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    try:
        db.delete(message)
        db.commit()

        return {
            "status": "success",
            "message": "Message deleted",
            "deleted_message_id": message_id
        }

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to delete message")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete message"
        )


# =========================
# Customer CRUD
# =========================

@app.post("/customers", status_code=201)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db)
):
    if customer.telegram_id is not None:
        existing_customer = db.query(Customer).filter(
            Customer.telegram_id == customer.telegram_id
        ).first()

        if existing_customer:
            raise HTTPException(
                status_code=409,
                detail="Customer with this Telegram ID already exists"
            )

    try:
        new_customer = Customer(**customer.model_dump())
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)

        return {
            "status": "success",
            "customer": {
                "id": new_customer.id,
                "telegram_id": new_customer.telegram_id,
                "username": new_customer.username,
                "full_name": new_customer.full_name
            }
        }

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to create customer")
        raise HTTPException(
            status_code=500,
            detail="Failed to create customer"
        )


@app.get("/customers")
def get_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).order_by(Customer.id).all()
    return {
        "total": len(customers),
        "customers": customers
    }


@app.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


@app.put("/customers/{customer_id}")
def update_customer(
    customer_id: int,
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    if customer_data.telegram_id is not None:
        existing_customer = db.query(Customer).filter(
            Customer.telegram_id == customer_data.telegram_id,
            Customer.id != customer_id
        ).first()

        if existing_customer:
            raise HTTPException(
                status_code=409,
                detail="Telegram ID already belongs to another customer"
            )

    try:
        customer.telegram_id = customer_data.telegram_id
        customer.username = customer_data.username
        customer.full_name = customer_data.full_name

        db.commit()
        db.refresh(customer)

        return {
            "status": "success",
            "customer": {
                "id": customer.id,
                "telegram_id": customer.telegram_id,
                "username": customer.username,
                "full_name": customer.full_name
            }
        }

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to update customer")
        raise HTTPException(
            status_code=500,
            detail="Failed to update customer"
        )


# =========================
# Telegram Event API
# =========================

@app.post("/telegram/events", status_code=201)
def create_telegram_event(
    event: TelegramEventCreate,
    db: Session = Depends(get_db)
):
    try:
        customer = db.query(Customer).filter(
            Customer.telegram_id == event.telegram_id
        ).first()

        if customer is None:
            customer = Customer(
                telegram_id=event.telegram_id,
                username=event.username,
                full_name=event.full_name
            )
            db.add(customer)
            db.flush()
        else:
            customer.username = event.username
            customer.full_name = event.full_name

        telegram_message = TelegramMessage(
            customer_id=customer.id,
            telegram_chat_id=event.chat_id,
            telegram_message_id=event.telegram_message_id,
            direction=event.direction,
            message=event.message
        )

        db.add(telegram_message)
        db.commit()
        db.refresh(telegram_message)

        return {
            "status": "success",
            "customer_id": customer.id,
            "telegram_message_id": telegram_message.id,
            "direction": telegram_message.direction
        }

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to save Telegram event")
        raise HTTPException(
            status_code=500,
            detail="Failed to save Telegram event"
        )


# =========================
# Order Lookup Tool API
# =========================

@app.post("/orders/lookup")
def lookup_customer_order(
    data: OrderLookupRequest,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_internal_api_key)
):
    order = (
        db.query(Order)
        .join(Customer, Order.customer_id == Customer.id)
        .filter(
            Customer.telegram_id == data.telegram_id,
            Order.tracking_number == data.tracking_number
        )
        .first()
    )

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order.id,
        "customer_id": order.customer_id,
        "status": order.status,
        "total_price": str(order.total_price),
        "order_date": order.order_date,
        "tracking_number": order.tracking_number
    }


# =========================
# Customer Lookup Tool API
# =========================

@app.get("/customers/lookup")
def lookup_customer_by_telegram(
    telegram_id: int,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_internal_api_key)
):
    if telegram_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Invalid Telegram ID"
        )

    customer = db.query(Customer).filter(
        Customer.telegram_id == telegram_id
    ).first()

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {
        "customer_id": customer.id,
        "telegram_id": customer.telegram_id,
        "username": customer.username,
        "full_name": customer.full_name
    }
