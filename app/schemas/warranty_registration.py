from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WarrantyRegistrationBase(BaseModel):
    policy_id: int
    product_id: int
    serial_number: str = Field(min_length=1, max_length=120)
    purchase_invoice_id: Optional[int] = None
    purchase_source: str = Field(min_length=1, max_length=50)
    purchase_date: datetime


class WarrantyRegistrationCreate(WarrantyRegistrationBase):
    pass


class WarrantyRegistrationUpdate(BaseModel):
    warranty_status: Optional[str] = Field(default=None, pattern="^(PENDING|ACTIVE|EXPIRED|CANCELLED)$")
    notes: Optional[str] = None


class WarrantyRegistrationResponse(WarrantyRegistrationBase):
    id: int
    user_id: int
    warranty_start_date: datetime
    warranty_end_date: datetime
    warranty_status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)