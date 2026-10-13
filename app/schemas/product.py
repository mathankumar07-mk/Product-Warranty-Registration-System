from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from pydantic import BaseModel, ConfigDict, Field

ProductPrice = Annotated[Decimal, Field(ge=0, decimal_places=2)]


class ProductBase(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=180)
    description: Optional[str] = None
    price: ProductPrice
    stock_quantity: int = Field(ge=0, default=0)
    brand: str = Field(min_length=1, max_length=120)
    model_number: str = Field(min_length=1, max_length=120)
    image_url: Optional[str] = Field(default=None, max_length=500)
    warranty_available: bool = False

    model_config = ConfigDict(protected_namespaces=())


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    category_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=180)
    description: Optional[str] = None
    price: Optional[ProductPrice] = None
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    brand: Optional[str] = Field(default=None, min_length=1, max_length=120)
    model_number: Optional[str] = Field(default=None, min_length=1, max_length=120)
    image_url: Optional[str] = Field(default=None, max_length=500)
    warranty_available: Optional[bool] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int