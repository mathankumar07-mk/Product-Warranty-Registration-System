from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class WarrantyPolicy(Base):
    __tablename__ = "warranty_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    warranty_period_months = Column(Integer, nullable=False)
    terms = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    product = relationship("Product", back_populates="warranty_policy")
    registrations = relationship("WarrantyRegistration", back_populates="policy")