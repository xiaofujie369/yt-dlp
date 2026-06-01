from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.enums import RuleType, UserRole, UserStatus


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

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is not None and value not in {role.value for role in UserRole}:
            raise ValueError("role must be one of user, vip, admin")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in {status.value for status in UserStatus}:
            raise ValueError("status must be one of active, disabled")
        return value

    @field_validator("daily_quota", "used_today")
    @classmethod
    def validate_non_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("quota values cannot be negative")
        return value


class DomainRuleIn(BaseModel):
    domain: str
    rule_type: str
    status: str = "active"
    remark: str | None = None

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, value: str) -> str:
        if value not in {rule.value for rule in RuleType}:
            raise ValueError("rule_type must be allow or deny")
        return value

    @field_validator("status")
    @classmethod
    def validate_rule_status(cls, value: str) -> str:
        if value not in {"active", "disabled"}:
            raise ValueError("status must be active or disabled")
        return value


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
