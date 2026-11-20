from sqlalchemy import select

from app.database.connection import SessionLocal
from app.database.models import Customer

with SessionLocal() as db:

    customer = db.scalar(
        select(Customer).where(
            Customer.id == 4
        )
    )

    if customer:
        customer.telegram_id = 123456789
        db.commit()

        print("Customer Telegram ID updated successfully!")

    else:
        print("Customer not found!")