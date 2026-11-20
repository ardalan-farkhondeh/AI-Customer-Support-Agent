
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Order

def get_order_status(
    db: Session,
    order_id: int,
    customer_id: int
):
    """
    Retrieve an order status for a specific customer.
    """

    statement = select(Order).where(
        Order.id == order_id,
        Order.customer_id == customer_id
    )

    order = db.execute(statement).scalar_one_or_none()

    if order is None:
        return {
            "success": False,
            "message": "Order not found."
        }

    return {
        "success": True,
        "order_id": order.id,
        "status": order.status,
        "total_price": float(order.total_price),
        "tracking_number": order.tracking_number
    }
