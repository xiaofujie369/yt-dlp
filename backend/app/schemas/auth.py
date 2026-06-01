from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    koyun_user_id: str
    email: str | None
    username: str
    avatar: str | None
    role: str
    status: str
    daily_quota: int
    used_today: int
    max_concurrent_tasks: int
    max_file_size_mb: int
    max_duration_minutes: int
    file_retention_hours: int
    allow_video: bool
    allow_audio: bool
    allow_thumbnail: bool
    allow_subtitle: bool
    allow_playlist: bool
    allow_batch: bool
    allowed_platforms: str | None
    denied_platforms: str | None
    remark: str | None
    banned_reason: str | None
    banned_until: datetime | None
