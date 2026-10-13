from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AdminBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class AdminCreate(AdminBase):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_bcrypt_password_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class AdminResponse(AdminBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)