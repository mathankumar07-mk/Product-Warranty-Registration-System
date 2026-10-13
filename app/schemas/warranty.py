from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WarrantyPolicyBase(BaseModel):
    product_id: int
    warranty_period_months: int = Field(ge=1)
    terms: str = Field(min_length=1)


class WarrantyPolicyCreate(WarrantyPolicyBase):
    pass


class WarrantyPolicyUpdate(BaseModel):
    warranty_period_months: Optional[int] = Field(default=None, ge=1)
    terms: Optional[str] = Field(default=None, min_length=1)


class WarrantyPolicyResponse(WarrantyPolicyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)