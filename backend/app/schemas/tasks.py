from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import TaskStatus, TaskType


class TaskCreate(BaseModel):
    url: str = Field(min_length=8, max_length=4000)
    task_type: TaskType = TaskType.VIDEO
    quality: str = "best"


class TaskCreated(BaseModel):
    task_id: str
    status: TaskStatus


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    url: str
    domain: str
    platform: str | None
    task_type: str
    status: str
    progress: float
    title: str | None
    filename: str | None
    file_size: int | None
    duration: float | None
    format: str | None
    quality: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    expired_at: datetime | None
    file_id: int | None = None
    created_at: datetime
    updated_at: datetime


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    filename: str
    file_size: int
    mime_type: str | None
    download_count: int
    expired_at: datetime | None
    status: str
    created_at: datetime
