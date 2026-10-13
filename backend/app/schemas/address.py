from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AddressBase(BaseModel):
    label: str = Field(min_length=1, max_length=50)
    line1: str = Field(min_length=1, max_length=200)
    line2: Optional[str] = Field(default=None, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=100)
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=50)
    line1: Optional[str] = Field(default=None, min_length=1, max_length=200)
    line2: Optional[str] = Field(default=None, max_length=200)
    city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, min_length=1, max_length=100)
    postal_code: Optional[str] = Field(default=None, min_length=1, max_length=20)
    country: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_default: Optional[bool] = None


class AddressResponse(AddressBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)