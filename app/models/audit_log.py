from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.core.database import Base


class AuditLog(Base):
    """Immutable record of admin actions. Never updated or deleted via API."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("admins.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(120), nullable=False, index=True)
    entity_type = Column(String(80), nullable=True, index=True)
    entity_id = Column(String(80), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    admin = relationship("Admin", back_populates="audit_logs")
