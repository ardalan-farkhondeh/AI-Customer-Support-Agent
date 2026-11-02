
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.database.models import Message, Customer

app = FastAPI(
    title="AI Customer Support Agent",
    description="AI-powered customer support system",
    version="0.1.0"
)


# Pydantic Model

class MessageCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    message: str = Field(min_length=4, max_length=1000)


# GET - Home

@app.get("/")
def home():
    return {
        "message": "AI Customer Support Agent is running"
    }


# GET - Health Check

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# POST - Create Message

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


# GET - Get All Messages

@app.get("/messages")
def get_messages(db: Session = Depends(get_db)):

    messages = db.query(Message).order_by(Message.id).all()

    return {
        "total": len(messages),
        "messages": messages
    }


# GET - Get Single Message

@app.get("/messages/{message_id}")
def get_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    message = db.get(Message, message_id)

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )

    return message


# DELETE - Delete Message

@app.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    message = db.get(Message, message_id)

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )

    db.delete(message)
    db.commit()

    return {
        "status": "success",
        "message": "Message deleted",
        "deleted_message_id": message_id
    }


# PUT - Update Message

@app.put("/messages/{message_id}")
def update_message(
    message_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    message = db.get(Message, message_id)

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )

    message.name = message_data.name
    message.email = message_data.email
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

    
# Pydantic Model - Customer

class CustomerCreate(BaseModel):
    telegram_id: int | None = None
    username: str | None = Field(default=None, max_length=100)
    full_name: str | None = Field(default=None, max_length=200)





# POST - Create Customer

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



# GET - Get All Customers

@app.get("/customers")
def get_customers(db: Session = Depends(get_db)):

    customers = db.query(Customer).order_by(Customer.id).all()

    return {
        "total": len(customers),
        "customers": customers
    }


# GET - Get Single Customer

@app.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer



# PUT - Update Customer

@app.put("/customers/{customer_id}")
def update_customer(
    customer_id: int,
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

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
