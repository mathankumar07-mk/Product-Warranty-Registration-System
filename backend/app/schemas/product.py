from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=180)
    description: Optional[str] = None
    price: Decimal = Field(ge=0, decimal_places=2)
    stock_quantity: int = Field(ge=0, default=0)
    brand: str = Field(min_length=1, max_length=120)
    model_number: str = Field(min_length=1, max_length=120)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=180)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    brand: Optional[str] = Field(default=None, min_length=1, max_length=120)
    model_number: Optional[str] = Field(default=None, min_length=1, max_length=120)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)