import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import func

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import TaskStatus
from app.models.all_models import DailyStat, DownloadFile, DownloadTask, OperationLog, User


def reset_daily_quotas() -> None:
    db = SessionLocal()
    try:
        db.query(User).update({User.used_today: 0})
        db.commit()
    finally:
        db.close()


def cleanup_expired_files() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(UTC)
        files = db.query(DownloadFile).filter(DownloadFile.status == "active", DownloadFile.expired_at <= now).all()
        for file in files:
            path = Path(file.file_path)
            if path.exists() and Path(settings.download_dir).resolve() in path.resolve().parents:
                path.unlink()
            file.status = "expired"
            task = db.get(DownloadTask, file.task_id)
            if task and task.status == TaskStatus.COMPLETED:
                task.status = TaskStatus.EXPIRED
        db.commit()
    finally:
        db.close()


def generate_daily_stats() -> None:
    db = SessionLocal()
    try:
        target = date.today() - timedelta(days=1)
        start = datetime.combine(target, datetime.min.time(), tzinfo=UTC)
        end = start + timedelta(days=1)
        query = db.query(DownloadTask).filter(DownloadTask.created_at >= start, DownloadTask.created_at < end)
        stat = db.query(DailyStat).filter(DailyStat.date == target).first() or DailyStat(date=target)
        stat.total_tasks = query.count()
        stat.success_tasks = query.filter(DownloadTask.status == TaskStatus.COMPLETED).count()
        stat.failed_tasks = query.filter(DownloadTask.status == TaskStatus.FAILED).count()
        stat.total_file_size = query.with_entities(func.coalesce(func.sum(DownloadTask.file_size), 0)).scalar() or 0
        stat.total_users = db.query(User).count()
        stat.active_users = db.query(func.count(func.distinct(DownloadTask.user_id))).filter(DownloadTask.created_at >= start, DownloadTask.created_at < end).scalar() or 0
        db.add(stat)
        db.commit()
    finally:
        db.close()


def mark_stalled_tasks() -> None:
    db = SessionLocal()
    try:
        cutoff = datetime.now(UTC) - timedelta(seconds=settings.task_timeout_seconds)
        stalled = (
            db.query(DownloadTask)
            .filter(DownloadTask.status.in_(["queued", "downloading", "merging", "transcoding"]), DownloadTask.updated_at < cutoff)
            .all()
        )
        for task in stalled:
            task.status = TaskStatus.FAILED
            task.error_message = "Task timed out or worker stopped reporting progress"
            task.completed_at = datetime.now(UTC)
        db.commit()
    finally:
        db.close()


def cleanup_old_logs() -> None:
    db = SessionLocal()
    try:
        cutoff = datetime.now(UTC) - timedelta(days=90)
        db.query(OperationLog).filter(OperationLog.created_at < cutoff).delete()
        db.commit()
    finally:
        db.close()


def main() -> None:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(reset_daily_quotas, "cron", hour=0, minute=0)
    scheduler.add_job(cleanup_expired_files, "interval", hours=1, next_run_time=datetime.now(UTC))
    scheduler.add_job(generate_daily_stats, "cron", hour=0, minute=10)
    scheduler.add_job(mark_stalled_tasks, "interval", hours=1)
    scheduler.add_job(cleanup_old_logs, "cron", hour=0, minute=30)
    scheduler.start()


if __name__ == "__main__":
    main()
