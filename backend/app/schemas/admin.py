from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class AdminCreate(AdminBase):
    password: str = Field(min_length=8, max_length=128)


class AdminResponse(AdminBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)