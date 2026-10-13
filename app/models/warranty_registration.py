from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class WarrantyStatus(str, PyEnum):
    PENDING = "PENDING"
    PENDING_REVIEW = "PENDING_REVIEW"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class PurchaseSource(str, PyEnum):
    COMPANY_WEBSITE = "Company Website"
    AMAZON = "Amazon"
    FLIPKART = "Flipkart"
    CROMA = "Croma"
    RELIANCE_DIGITAL = "Reliance Digital"
    OFFLINE_STORE = "Offline Store"
    OTHER = "Other"


class WarrantyRegistration(Base):
    __tablename__ = "warranty_registrations"
    __table_args__ = (
        UniqueConstraint("product_id", "serial_number", name="uq_warranty_product_serial"),
        UniqueConstraint("purchase_invoice_id", "product_id", name="uq_warranty_invoice_product"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    warranty_number = Column(String(32), nullable=True, unique=True, index=True)
    policy_id = Column(Integer, ForeignKey("warranty_policies.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_invoice_id = Column(Integer, ForeignKey("purchase_invoices.id", ondelete="RESTRICT"), nullable=True)
    serial_number = Column(String(120), nullable=False)
    purchase_source = Column(Enum(PurchaseSource), nullable=False)
    proof_reference = Column(String(255), nullable=True)
    purchase_date = Column(DateTime, nullable=False)
    warranty_start_date = Column(DateTime, nullable=False)
    warranty_end_date = Column(DateTime, nullable=False)
    warranty_status = Column(Enum(WarrantyStatus), nullable=False, default=WarrantyStatus.PENDING)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    policy = relationship("WarrantyPolicy", back_populates="registrations")
    user = relationship("User", back_populates="warranty_registrations")
    product = relationship("Product", back_populates="warranty_registrations")