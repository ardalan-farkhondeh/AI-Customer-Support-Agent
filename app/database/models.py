
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    BigInteger,
    DateTime,
    Text,
    Numeric,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# =========================
# Base Model
# =========================

class Base(DeclarativeBase):
    pass


# =========================
# Customer Model
# =========================

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    telegram_id: Mapped[int | None] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True,
        index=True
    )

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    full_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    telegram_messages: Mapped[list["TelegramMessage"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# =========================
# Contact Message Model
# =========================

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )


# =========================
# Telegram Message Model
# =========================

class TelegramMessage(Base):
    __tablename__ = "telegram_messages"

    __table_args__ = (
        UniqueConstraint(
            "telegram_chat_id",
            "telegram_message_id",
            name="uq_telegram_chat_message"
        ),
        CheckConstraint(
            "direction IN ('incoming', 'outgoing')",
            name="check_telegram_message_direction"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    telegram_chat_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True
    )

    telegram_message_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )

    direction: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="telegram_messages"
    )


# =========================
# Order Model
# =========================

class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'shipped', "
            "'delivered', 'cancelled')",
            name="check_order_status"
        ),
        CheckConstraint(
            "total_price >= 0",
            name="check_order_total_price"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending"
    )

    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="orders"
    )
