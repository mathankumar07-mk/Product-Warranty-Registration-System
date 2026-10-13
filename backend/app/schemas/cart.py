from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(CartItemBase):
    id: int
    cart_id: int
    product: "ProductResponse"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: list[CartItemResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)