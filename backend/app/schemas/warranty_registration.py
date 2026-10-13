from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WarrantyStatus(str, Enum):
    pending = "pending"
    active = "active"
    expired = "expired"


class PurchaseSource(str, Enum):
    online = "online"
    in_store = "in_store"
    other = "other"


class WarrantyRegistrationBase(BaseModel):
    policy_id: int
    product_id: int
    serial_number: str = Field(min_length=1, max_length=120)
    purchase_invoice_id: Optional[int] = None
    purchase_source: PurchaseSource = PurchaseSource.other
    purchase_date: datetime


class WarrantyRegistrationCreate(WarrantyRegistrationBase):
    pass


class WarrantyRegistrationUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(pending|approved|rejected)$")
    warranty_status: Optional[WarrantyStatus] = None
    notes: Optional[str] = None


class WarrantyRegistrationResponse(WarrantyRegistrationBase):
    id: int
    user_id: int
    purchase_source: PurchaseSource
    purchase_date: datetime
    warranty_start_date: datetime
    warranty_end_date: datetime
    warranty_status: WarrantyStatus
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)