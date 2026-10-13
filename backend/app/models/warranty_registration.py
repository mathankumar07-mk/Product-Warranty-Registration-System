from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class WarrantyStatus(str, PyEnum):
    pending = "pending"
    active = "active"
    expired = "expired"


class PurchaseSource(str, PyEnum):
    online = "online"
    in_store = "in_store"
    other = "other"


class RegistrationStatus(str, PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class WarrantyRegistration(Base):
    __tablename__ = "warranty_registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(Integer, ForeignKey("warranty_policies.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_invoice_id = Column(Integer, ForeignKey("purchase_invoices.id", ondelete="RESTRICT"), nullable=True)
    serial_number = Column(String(120), nullable=False)
    purchase_source = Column(Enum(PurchaseSource), nullable=False, default=PurchaseSource.other)
    purchase_date = Column(DateTime, nullable=False)
    warranty_start_date = Column(DateTime, nullable=False)
    warranty_end_date = Column(DateTime, nullable=False)
    warranty_status = Column(Enum(WarrantyStatus), nullable=False, default=WarrantyStatus.pending)
    status = Column(Enum(RegistrationStatus), nullable=False, default=RegistrationStatus.pending)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    policy = relationship("WarrantyPolicy", back_populates="registrations")
    user = relationship("User", back_populates="warranty_registrations")
    product = relationship("Product", back_populates="warranty_registrations")