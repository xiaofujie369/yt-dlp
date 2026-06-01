from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from redis import Redis
from rq import Queue
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import TaskStatus, TaskType, UserRole
from app.models.all_models import DomainRule, DownloadFile, DownloadTask, User
from app.schemas.tasks import TaskCreate
from app.services.user_permissions import enforce_user_download_permissions
from app.utils.url import domain_matches, parse_public_url

ACTIVE_STATUSES = [
    TaskStatus.QUEUED,
    TaskStatus.DOWNLOADING,
    TaskStatus.MERGING,
    TaskStatus.TRANSCODING,
    "pending",
    "running",
    "processing",
]
CANCELLABLE_STATUSES = {str(status) for status in ACTIVE_STATUSES}
RETRYABLE_STATUSES = {str(TaskStatus.FAILED), str(TaskStatus.CANCELLED), "failed", "cancelled"}
NON_CANCELLABLE_STATUSES = {
    str(TaskStatus.COMPLETED),
    str(TaskStatus.FAILED),
    str(TaskStatus.CANCELLED),
    str(TaskStatus.EXPIRED),
    str(TaskStatus.DELETED),
}


def get_queue(redis: Redis, user: User | None = None) -> Queue:
    queue_name = "downloads:vip" if user and user.role == UserRole.VIP else "downloads"
    return Queue(queue_name, connection=redis, default_timeout=settings.task_timeout_seconds + 120)


def create_task(db: Session, redis: Redis, user: User, payload: TaskCreate, client_ip: str | None, user_agent: str | None) -> DownloadTask:
    raw_url, domain = parse_public_url(payload.url)
    enforce_domain_rules(db, domain)
    enforce_user_download_permissions(db, user, payload.task_type, raw_url, domain)
    if payload.task_type == TaskType.AUDIO and not _setting_bool(db, "allow_mp3", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MP3 downloads are disabled")
    if payload.task_type == TaskType.SUBTITLE and not _setting_bool(db, "allow_subtitle", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Subtitle downloads are disabled")

    task = DownloadTask(
        task_id=str(uuid4()),
        user_id=user.id,
        url=raw_url,
        domain=domain,
        platform=domain,
        task_type=payload.task_type,
        status=TaskStatus.QUEUED,
        quality=payload.quality,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    user.used_today += 1
    user.total_tasks += 1
    db.add(task)
    db.flush()
    get_queue(redis, user).enqueue("app.workers.downloader.download_task", task.task_id, job_id=task.task_id)
    db.commit()
    return task


def enforce_domain_rules(db: Session, domain: str) -> None:
    rules = db.query(DomainRule).filter(DomainRule.status == "active").all()
    deny_rules = [rule for rule in rules if rule.rule_type == "deny"]
    allow_rules = [rule for rule in rules if rule.rule_type == "allow"]
    if any(domain_matches(rule.domain, domain) for rule in deny_rules):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Domain is denied")
    if allow_rules and not any(domain_matches(rule.domain, domain) for rule in allow_rules):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Domain is not in the allow list")


def enforce_user_quota(db: Session, user: User) -> None:
    if user.used_today >= user.daily_quota:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Daily download quota exceeded")


def enforce_user_concurrency(db: Session, user: User) -> None:
    active = (
        db.query(func.count(DownloadTask.id))
        .filter(DownloadTask.user_id == user.id, DownloadTask.status.in_([str(item) for item in ACTIVE_STATUSES]))
        .scalar()
    )
    if active >= user.max_concurrent_tasks:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many active tasks")


def list_user_tasks(db: Session, user: User, page: int, page_size: int) -> tuple[list[DownloadTask], int]:
    query = db.query(DownloadTask).filter(DownloadTask.user_id == user.id, DownloadTask.status != TaskStatus.DELETED)
    total = query.count()
    items = query.order_by(DownloadTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_user_task(db: Session, user: User, task_id: str) -> DownloadTask:
    task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id, DownloadTask.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def cancel_task(db: Session, redis: Redis, task: DownloadTask) -> DownloadTask:
    if task.status in NON_CANCELLABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Task in {task.status} status cannot be cancelled")
    if task.status not in CANCELLABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Task in {task.status} status cannot be cancelled")

    now = datetime.now(UTC)
    redis.set(f"task:{task.task_id}:cancel", "1", ex=settings.task_timeout_seconds)
    task.status = TaskStatus.CANCELLED
    task.cancelled_at = now
    task.completed_at = now
    task.error_message = None

    job = get_queue(redis).fetch_job(task.task_id) or Queue("downloads:vip", connection=redis).fetch_job(task.task_id)
    if job:
        job.cancel()
    db.commit()
    return task


def retry_task(db: Session, redis: Redis, task: DownloadTask) -> DownloadTask:
    if task.status not in RETRYABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Task in {task.status} status cannot be retried")

    redis.delete(f"task:{task.task_id}:cancel")
    for queue in (get_queue(redis), Queue("downloads:vip", connection=redis)):
        existing_job = queue.fetch_job(task.task_id)
        if existing_job:
            existing_job.delete()

    task.status = TaskStatus.QUEUED
    task.progress = 0
    task.error_message = None
    task.started_at = None
    task.completed_at = None
    task.cancelled_at = None
    get_queue(redis, task.user).enqueue("app.workers.downloader.download_task", task.task_id, job_id=task.task_id)
    db.commit()
    return task


def soft_delete_task(db: Session, task: DownloadTask) -> None:
    task.status = TaskStatus.DELETED
    db.commit()


def get_download_file(db: Session, user: User, file_id: int) -> DownloadFile:
    file = db.get(DownloadFile, file_id)
    if not file or file.user_id != user.id or file.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    base = Path(settings.download_dir).resolve()
    target = Path(file.file_path).resolve()
    if base not in target.parents and target != base:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid file path")
    if file.expired_at and file.expired_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="File has expired")
    if not target.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File no longer exists")
    file.download_count += 1
    db.commit()
    return file


def mark_task_completed(db: Session, task: DownloadTask, file_path: Path, file_size: int) -> None:
    retention_hours = task.user.file_retention_hours
    expires_at = datetime.now(UTC) + timedelta(hours=retention_hours)
    task.status = TaskStatus.COMPLETED
    task.progress = 100
    task.file_path = str(file_path)
    task.filename = file_path.name
    task.file_size = file_size
    task.completed_at = datetime.now(UTC)
    task.expired_at = expires_at
    task.user.success_tasks += 1
    db.add(
        DownloadFile(
            task_id=task.id,
            user_id=task.user_id,
            filename=file_path.name,
            file_path=str(file_path),
            file_size=file_size,
            expired_at=expires_at,
            mime_type="audio/mpeg" if file_path.suffix == ".mp3" else "video/mp4",
        )
    )


def _setting_bool(db: Session, key: str, default: bool) -> bool:
    from app.services.settings import get_bool_setting

    return get_bool_setting(db, key, default)
