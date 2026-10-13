from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PurchaseInvoiceBase(BaseModel):
    order_id: int
    invoice_number: str = Field(min_length=1, max_length=50)
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    tax_amount: Decimal = Field(ge=0, decimal_places=2, default=Decimal("0.00"))
    file_path: Optional[str] = Field(default=None, max_length=500)


class PurchaseInvoiceCreate(PurchaseInvoiceBase):
    pass


class PurchaseInvoiceUpdate(BaseModel):
    file_path: Optional[str] = Field(default=None, max_length=500)


class PurchaseInvoiceResponse(PurchaseInvoiceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)