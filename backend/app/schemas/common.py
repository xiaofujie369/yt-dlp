from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIError(BaseModel):
    code: str
    message: str
    detail: dict | None = None


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class Timestamped(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime
