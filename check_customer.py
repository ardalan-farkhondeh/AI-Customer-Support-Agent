from sqlalchemy import select

from app.database.connection import SessionLocal
from app.database.models import Customer

with SessionLocal() as db:

    customers = db.scalars(
        select(Customer).where(
            Customer.telegram_id == 123456789
        )
    ).all()

    for customer in customers:
        print("Customer ID:", customer.id)
        print("Telegram ID:", customer.telegram_id)
        print("Username:", customer.username)
        print("Full Name:", customer.full_name)
        print("----------------------")