
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field


app = FastAPI(
    title="AI Customer Support Agent",
    description="AI-powered customer support system",
    version="0.1.0"
)


# Pydantic Models

class MessageCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    message: str = Field(min_length=4, max_length=1000)


# In-Memory Database

messages_db = []


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

@app.post(
    "/messages",
    status_code=201,
    responses={
        400: {"description": "Test message is not allowed"}
    }
)
def create_message(message: MessageCreate):

    if message.message.strip().lower() == "test":
        raise HTTPException(
            status_code=400,
            detail="Test message is not allowed"
        )

    new_message = {
        "id": len(messages_db) + 1,
        **message.model_dump()
    }

    messages_db.append(new_message)

    return {
        "status": "success",
        "message": new_message
    }


# GET - Get All Messages

@app.get("/messages")
def get_messages():
    return {
        "total": len(messages_db),
        "messages": messages_db
    }


# GET - Get Single Message

@app.get("/messages/{message_id}")
def get_message(message_id: int):

    for message in messages_db:
        if message["id"] == message_id:
            return message

    raise HTTPException(
        status_code=404,
        detail="Message not found"
    )


# PUT - Replace User

@app.put("/users/{user_id}")
def replace_user(user_id: int):
    return {
        "message": "User replaced",
        "user_id": user_id
    }


# PATCH - Update User

@app.patch("/users/{user_id}")
def update_user(user_id: int):
    return {
        "message": "User updated",
        "user_id": user_id
    }


# DELETE - Delete Message

@app.delete("/messages/{message_id}")
def delete_message(message_id: int):

    for index, message in enumerate(messages_db):
        if message["id"] == message_id:

            deleted_message = messages_db.pop(index)

            return {
                "status": "success",
                "message": "Message deleted",
                "deleted_message": deleted_message
            }

    raise HTTPException(
        status_code=404,
        detail="Message not found"
    )
