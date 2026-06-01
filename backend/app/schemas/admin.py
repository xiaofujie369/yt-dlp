from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DashboardOut(BaseModel):
    today_tasks: int
    today_success: int
    today_failed: int
    today_bytes: int
    queued_tasks: int
    downloading_tasks: int
    disk_used_bytes: int
    redis_status: str
    worker_status: str
    ytdlp_version: str
    ffmpeg_available: bool
    recent_daily: list[dict]
    popular_platforms: list[dict]
    failure_reasons: list[dict]


class UserPatch(BaseModel):
    role: str | None = None
    status: str | None = None
    daily_quota: int | None = None
    used_today: int | None = None


class DomainRuleIn(BaseModel):
    domain: str
    rule_type: str
    status: str = "active"
    remark: str | None = None


class DomainRuleOut(DomainRuleIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class IPBlacklistIn(BaseModel):
    ip: str | None = None
    cidr: str | None = None
    reason: str | None = None
    expired_at: datetime | None = None
    status: str = "active"


class IPBlacklistOut(IPBlacklistIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class SettingPatch(BaseModel):
    key: str
    value: str
    type: str = "string"
    description: str | None = None
