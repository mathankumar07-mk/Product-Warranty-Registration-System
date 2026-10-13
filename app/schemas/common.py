from typing import Generic, TypeVar
from pydantic import BaseModel

DataT = TypeVar("DataT")


class ErrorResponse(BaseModel):
    detail: str


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: list[DataT]
    total: int
    page: int
    page_size: int
    total_pages: int