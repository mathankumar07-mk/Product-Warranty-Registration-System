from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductResponse


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=0, decimal_places=2)


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    product: ProductResponse

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    shipping_address_id: Optional[int] = None
    billing_address_id: Optional[int] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(pending|confirmed|shipped|delivered|cancelled)$")
    shipping_address_id: Optional[int] = None
    billing_address_id: Optional[int] = None


class OrderResponse(OrderBase):
    id: int
    order_number: Optional[str] = None
    user_id: int
    status: str
    total_amount: Decimal
    items: list[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)