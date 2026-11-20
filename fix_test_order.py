from sqlalchemy import select

from app.database.connection import SessionLocal
from app.database.models import Order

with SessionLocal() as db:

    order = db.scalar(
        select(Order).where(
            Order.tracking_number == "TEST-ORDER-001"
        )
    )

    if order:
        order.customer_id = 1
        db.commit()

        print("Order successfully assigned to customer 1!")

    else:
        print("Order not found!")