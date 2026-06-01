from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.enums import TaskStatus, TaskType, UserRole, UserStatus
from app.models.all_models import DownloadTask, User
from app.utils.url import domain_matches, normalize_domain

ACTIVE_TASK_STATUSES = ["pending", "queued", "running", "downloading", "processing", "merging", "transcoding"]


ROLE_PERMISSION_TEMPLATES = {
    UserRole.USER: {
        "daily_quota": 5,
        "max_concurrent_tasks": 1,
        "max_file_size_mb": 500,
        "max_duration_minutes": 60,
        "file_retention_hours": 24,
        "allow_video": True,
        "allow_audio": True,
        "allow_thumbnail": True,
        "allow_subtitle": True,
        "allow_playlist": False,
        "allow_batch": False,
    },
    UserRole.VIP: {
        "daily_quota": 50,
        "max_concurrent_tasks": 3,
        "max_file_size_mb": 2048,
        "max_duration_minutes": 180,
        "file_retention_hours": 72,
        "allow_video": True,
        "allow_audio": True,
        "allow_thumbnail": True,
        "allow_subtitle": True,
        "allow_playlist": True,
        "allow_batch": True,
    },
    UserRole.ADMIN: {
        "daily_quota": 999,
        "max_concurrent_tasks": 10,
        "max_file_size_mb": 10240,
        "max_duration_minutes": 720,
        "file_retention_hours": 168,
        "allow_video": True,
        "allow_audio": True,
        "allow_thumbnail": True,
        "allow_subtitle": True,
        "allow_playlist": True,
        "allow_batch": True,
    },
}


class PermissionDenied(HTTPException):
    def __init__(self, code: str, message: str, http_status: int = status.HTTP_403_FORBIDDEN):
        super().__init__(status_code=http_status, detail={"code": code, "message": message})


def apply_role_template(user: User) -> User:
    role = UserRole(user.role) if user.role in {role.value for role in UserRole} else UserRole.USER
    for key, value in ROLE_PERMISSION_TEMPLATES[role].items():
        setattr(user, key, value)
    return user


def enforce_user_download_permissions(db: Session, user: User, task_type: str, url: str, domain: str) -> None:
    now = datetime.now(UTC)
    if user.status == UserStatus.DISABLED:
        raise PermissionDenied("user_disabled", "账号已被禁用")
    if user.status == UserStatus.READONLY:
        raise PermissionDenied("readonly_user", "当前账号只允许查看历史任务，不能新建下载任务")
    if user.status == UserStatus.BANNED:
        if user.banned_until is None or user.banned_until > now:
            raise PermissionDenied("user_banned", user.banned_reason or "账号已被封禁")
        user.status = UserStatus.ACTIVE
        user.banned_reason = None
        user.banned_until = None
        db.flush()
    if user.status != UserStatus.ACTIVE:
        raise PermissionDenied("user_not_active", "账号状态不可创建下载任务")

    if user.used_today >= user.daily_quota:
        raise PermissionDenied("quota_exceeded", "今日下载额度已用完", status.HTTP_429_TOO_MANY_REQUESTS)

    active_count = (
        db.query(func.count(DownloadTask.id))
        .filter(DownloadTask.user_id == user.id, DownloadTask.status.in_(ACTIVE_TASK_STATUSES))
        .scalar()
    )
    if active_count >= user.max_concurrent_tasks:
        raise PermissionDenied("concurrency_limit_exceeded", "同时进行中的任务数已达上限", status.HTTP_429_TOO_MANY_REQUESTS)

    if task_type == TaskType.VIDEO and not user.allow_video:
        raise PermissionDenied("video_not_allowed", "当前账号不允许下载视频")
    if task_type == TaskType.AUDIO and not user.allow_audio:
        raise PermissionDenied("audio_not_allowed", "当前账号不允许提取音频")
    if task_type == TaskType.THUMBNAIL and not user.allow_thumbnail:
        raise PermissionDenied("thumbnail_not_allowed", "当前账号不允许下载封面")
    if task_type == TaskType.SUBTITLE and not user.allow_subtitle:
        raise PermissionDenied("subtitle_not_allowed", "当前账号不允许下载字幕")
    if looks_like_playlist(url) and not user.allow_playlist:
        raise PermissionDenied("playlist_not_allowed", "当前账号不允许下载播放列表")

    denied = parse_platform_list(user.denied_platforms)
    if any(domain_matches(rule, domain) for rule in denied):
        raise PermissionDenied("platform_denied", "该平台已被当前账号禁止")

    allowed = parse_platform_list(user.allowed_platforms)
    if allowed and not any(domain_matches(rule, domain) for rule in allowed):
        raise PermissionDenied("platform_not_allowed", "该平台不在当前账号允许列表中")


def parse_platform_list(value: str | None) -> list[str]:
    if not value:
        return []
    normalized = value.replace("\n", ",").replace(";", ",")
    return [normalize_domain(item.strip()) for item in normalized.split(",") if item.strip()]


def looks_like_playlist(url: str) -> bool:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return "list" in query or "/playlist" in parsed.path.lower()
