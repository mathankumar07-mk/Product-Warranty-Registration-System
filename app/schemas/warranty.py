from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WarrantyPolicyBase(BaseModel):
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    warranty_period_months: int = Field(ge=1, le=120)
    terms: str = Field(min_length=1)


class WarrantyPolicyCreate(WarrantyPolicyBase):
    pass


class WarrantyPolicyUpdate(BaseModel):
    warranty_period_months: Optional[int] = Field(default=None, ge=1, le=120)
    terms: Optional[str] = Field(default=None, min_length=1)
    is_active: Optional[bool] = None


class WarrantyPolicyResponse(WarrantyPolicyBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
