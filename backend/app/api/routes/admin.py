import shutil
import subprocess
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from redis import Redis
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.all_models import DailyStat, DomainRule, DownloadFile, DownloadTask, IPBlacklist, OperationLog, SystemSetting, User
from app.schemas.admin import DashboardOut, DomainRuleIn, DomainRuleOut, IPBlacklistIn, IPBlacklistOut, SettingPatch, UserPatch
from app.schemas.auth import UserOut
from app.schemas.common import Page
from app.schemas.tasks import FileOut, TaskOut
from app.services.audit import log_admin_action
from app.services.tasks import cancel_task, retry_task, soft_delete_task

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Annotated[Session, Depends(get_db)], redis: Annotated[Redis, Depends(get_redis)], _: Annotated[User, Depends(require_admin)]):
    today = datetime.now(UTC).date()
    start = datetime.combine(today, datetime.min.time(), tzinfo=UTC)
    today_query = db.query(DownloadTask).filter(DownloadTask.created_at >= start)
    ytdlp_version = _command_version(["yt-dlp", "--version"])
    ffmpeg_version = _command_version(["ffmpeg", "-version"])
    recent_daily = [
        {"date": row.date.isoformat(), "total_tasks": row.total_tasks, "success_tasks": row.success_tasks, "failed_tasks": row.failed_tasks}
        for row in db.query(DailyStat).order_by(DailyStat.date.desc()).limit(7).all()
    ]
    popular_platforms = [
        {"platform": platform or "unknown", "count": count}
        for platform, count in db.query(DownloadTask.platform, func.count(DownloadTask.id)).group_by(DownloadTask.platform).order_by(func.count(DownloadTask.id).desc()).limit(10)
    ]
    failure_reasons = [
        {"reason": reason or "unknown", "count": count}
        for reason, count in db.query(DownloadTask.error_message, func.count(DownloadTask.id)).filter(DownloadTask.status == "failed").group_by(DownloadTask.error_message).order_by(func.count(DownloadTask.id).desc()).limit(10)
    ]
    return DashboardOut(
        today_tasks=today_query.count(),
        today_success=today_query.filter(DownloadTask.status == "completed").count(),
        today_failed=today_query.filter(DownloadTask.status == "failed").count(),
        today_bytes=today_query.with_entities(func.coalesce(func.sum(DownloadTask.file_size), 0)).scalar() or 0,
        queued_tasks=db.query(DownloadTask).filter(DownloadTask.status == "queued").count(),
        downloading_tasks=db.query(DownloadTask).filter(DownloadTask.status.in_(["downloading", "merging", "transcoding"])).count(),
        disk_used_bytes=_directory_size(Path(settings.download_dir)),
        redis_status="ok" if redis.ping() else "down",
        worker_status="ok" if len(redis.smembers("workers:heartbeat")) > 0 else "unknown",
        ytdlp_version=ytdlp_version,
        ffmpeg_available=bool(ffmpeg_version),
        recent_daily=recent_daily,
        popular_platforms=popular_platforms,
        failure_reasons=failure_reasons,
    )


@router.get("/tasks", response_model=Page[TaskOut])
def admin_tasks(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = None,
    q: str | None = None,
) -> Page[TaskOut]:
    query = db.query(DownloadTask)
    if status_filter:
        query = query.filter(DownloadTask.status == status_filter)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(DownloadTask.task_id.ilike(like), DownloadTask.url.ilike(like), DownloadTask.domain.ilike(like)))
    total = query.count()
    items = query.order_by(DownloadTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def admin_task_detail(task_id: str, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)]):
    return _task_or_404(db, task_id)


@router.post("/tasks/{task_id}/cancel", response_model=TaskOut)
def admin_cancel_task(
    task_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    admin: Annotated[User, Depends(require_admin)],
):
    task = cancel_task(db, redis, _task_or_404(db, task_id))
    log_admin_action(db, admin, "task.cancel", "task", task_id, ip=request.client.host if request.client else None)
    db.commit()
    return task


@router.post("/tasks/{task_id}/retry", response_model=TaskOut)
def admin_retry_task(
    task_id: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    admin: Annotated[User, Depends(require_admin)],
):
    task = _task_or_404(db, task_id)
    task = retry_task(db, redis, task)
    log_admin_action(db, admin, "task.retry", "task", task_id, ip=request.client.host if request.client else None)
    db.commit()
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def admin_delete_task(task_id: str, db: Annotated[Session, Depends(get_db)], admin: Annotated[User, Depends(require_admin)]):
    soft_delete_task(db, _task_or_404(db, task_id))
    log_admin_action(db, admin, "task.delete", "task", task_id)
    db.commit()


@router.get("/users", response_model=Page[UserOut])
def users(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)], page: int = 1, page_size: int = 20):
    query = db.query(User)
    total = query.count()
    items = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/users/{user_id}", response_model=UserOut)
def user_detail(user_id: int, db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)]):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def patch_user(user_id: int, payload: UserPatch, db: Annotated[Session, Depends(get_db)], admin: Annotated[User, Depends(require_admin)]):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    log_admin_action(db, admin, "user.patch", "user", str(user_id))
    db.commit()
    return user


@router.get("/files", response_model=Page[FileOut])
def files(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)], page: int = 1, page_size: int = 20):
    query = db.query(DownloadFile)
    total = query.count()
    items = query.order_by(DownloadFile.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.delete("/files/{file_id}", status_code=204)
def delete_file(file_id: int, db: Annotated[Session, Depends(get_db)], admin: Annotated[User, Depends(require_admin)]):
    file = db.get(DownloadFile, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    file.status = "deleted"
    path = Path(file.file_path)
    if path.exists() and Path(settings.download_dir).resolve() in path.resolve().parents:
        path.unlink()
    log_admin_action(db, admin, "file.delete", "file", str(file_id))
    db.commit()


@router.get("/domain-rules", response_model=list[DomainRuleOut])
def domain_rules(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)]):
    return db.query(DomainRule).order_by(DomainRule.rule_type, DomainRule.domain).all()


@router.post("/domain-rules", response_model=DomainRuleOut)
def create_domain_rule(payload: DomainRuleIn, db: Annotated[Session, Depends(get_db)], admin: Annotated[User, Depends(require_admin)]):
    rule = DomainRule(**payload.model_dump())
    db.add(rule)
    log_admin_action(db, admin, "domain_rule.create", "domain_rule", payload.domain)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/domain-rules/{rule_id}", response_model=DomainRuleOut)
def patch_domain_rule(rule_id: int, payload: DomainRuleIn, db: Annotated[Session, Depends(get_db)], admin: Annotated[User, Depends(require_admin)]):
    rule = db.get(DomainRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Domain rule not found")
    for field, value in payload.model_dump().items():
        setattr(rule, field, value)
    log_admin_action(db, admin, "domain_rule.patch", "domain_rule", str(rule_id))
    db.commit()
    return rule


@router.delete("/domain-rules/{rule_id}", status_code=204)
def delete_domain_rule(rule_id: int, db: Annotated[Session, Depends(get_db)], admin: Annotated[User, Depends(require_admin)]):
    rule = db.get(DomainRule, rule_id)
    if rule:
        db.delete(rule)
        log_admin_action(db, admin, "domain_rule.delete", "domain_rule", str(rule_id))
        db.commit()


@router.get("/ip-blacklist", response_model=list[IPBlacklistOut])
def ip_blacklist(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)]):
    return db.query(IPBlacklist).order_by(IPBlacklist.created_at.desc()).all()


@router.post("/ip-blacklist", response_model=IPBlacklistOut)
def create_ip_blacklist(payload: IPBlacklistIn, db: Annotated[Session, Depends(get_db)], admin: Annotated[User, Depends(require_admin)]):
    record = IPBlacklist(**payload.model_dump())
    db.add(record)
    log_admin_action(db, admin, "ip_blacklist.create", "ip_blacklist", payload.ip or payload.cidr)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/ip-blacklist/{record_id}", status_code=204)
def delete_ip_blacklist(record_id: int, db: Annotated[Session, Depends(get_db)], admin: Annotated[User, Depends(require_admin)]):
    record = db.get(IPBlacklist, record_id)
    if record:
        db.delete(record)
        log_admin_action(db, admin, "ip_blacklist.delete", "ip_blacklist", str(record_id))
        db.commit()


@router.get("/settings")
def list_settings(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)]):
    return db.query(SystemSetting).order_by(SystemSetting.key).all()


@router.patch("/settings")
def patch_setting(payload: SettingPatch, db: Annotated[Session, Depends(get_db)], admin: Annotated[User, Depends(require_admin)]):
    setting = db.query(SystemSetting).filter(SystemSetting.key == payload.key).first()
    if not setting:
        setting = SystemSetting(key=payload.key)
        db.add(setting)
    setting.value = payload.value
    setting.type = payload.type
    setting.description = payload.description
    log_admin_action(db, admin, "setting.patch", "setting", payload.key)
    db.commit()
    return setting


@router.get("/stats/daily")
def daily_stats(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)]):
    return db.query(DailyStat).order_by(DailyStat.date.desc()).limit(90).all()


@router.get("/stats/weekly")
def weekly_stats(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)]):
    return _aggregate_stats(db, days=7)


@router.get("/stats/monthly")
def monthly_stats(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)]):
    return _aggregate_stats(db, days=30)


@router.get("/logs")
def logs(db: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_admin)], page: int = 1, page_size: int = 50):
    query = db.query(OperationLog)
    return {
        "items": query.order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all(),
        "total": query.count(),
        "page": page,
        "page_size": page_size,
    }


def _task_or_404(db: Session, task_id: str) -> DownloadTask:
    task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def _command_version(command: list[str]) -> str:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=5, check=False).stdout.splitlines()[0]
    except Exception:
        return ""


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _aggregate_stats(db: Session, days: int) -> dict:
    since = date.today() - timedelta(days=days)
    rows = db.query(DailyStat).filter(DailyStat.date >= since).all()
    return {
        "days": days,
        "total_tasks": sum(row.total_tasks for row in rows),
        "success_tasks": sum(row.success_tasks for row in rows),
        "failed_tasks": sum(row.failed_tasks for row in rows),
        "total_file_size": sum(row.total_file_size for row in rows),
    }
