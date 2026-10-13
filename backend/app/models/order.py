from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class OrderStatus(str, PyEnum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
    total_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    shipping_address_id = Column(Integer, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True)
    billing_address_id = Column(Integer, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order")
    invoice = relationship("PurchaseInvoice", back_populates="order", uselist=False, cascade="all, delete-orphan")