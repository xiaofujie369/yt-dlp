from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    VIP = "vip"
    ADMIN = "admin"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class TaskStatus(StrEnum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    TRANSCODING = "transcoding"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    DELETED = "deleted"


class TaskType(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"
    THUMBNAIL = "thumbnail"
    SUBTITLE = "subtitle"


class RuleType(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


TERMINAL_TASK_STATUSES = {
    TaskStatus.COMPLETED,
    TaskStatus.FAILED,
    TaskStatus.CANCELLED,
    TaskStatus.EXPIRED,
    TaskStatus.DELETED,
}
