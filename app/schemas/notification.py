from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    type: str = Field(pattern="^(order|payment|warranty|general)$")
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)