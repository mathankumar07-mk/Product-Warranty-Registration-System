from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PaymentBase(BaseModel):
    order_id: int
    amount: Decimal = Field(ge=0, decimal_places=2)
    method: str = Field(pattern="^(card|upi|netbanking|wallet|cod)$")


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(pending|completed|failed|refunded)$")
    transaction_id: Optional[str] = Field(default=None, max_length=120)


class PaymentResponse(PaymentBase):
    id: int
    status: str
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)