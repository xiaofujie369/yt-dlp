import os
import re
import subprocess
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

from redis import Redis

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import TaskStatus, TaskType
from app.models.all_models import DownloadTask
from app.services.settings import get_int_setting
from app.services.tasks import mark_task_completed

PROGRESS_RE = re.compile(r"\[download]\s+(\d+(?:\.\d+)?)%")


def download_task(task_id: str) -> None:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    db = SessionLocal()
    task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
    if not task:
        db.close()
        return
    if task.status == TaskStatus.CANCELLED or redis.get(f"task:{task.task_id}:cancel"):
        task.status = TaskStatus.CANCELLED
        task.cancelled_at = task.cancelled_at or datetime.now(UTC)
        task.completed_at = task.completed_at or task.cancelled_at
        db.commit()
        db.close()
        redis.close()
        return

    output_dir = Path(settings.download_dir) / task.task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    process: subprocess.Popen | None = None

    try:
        task.status = TaskStatus.DOWNLOADING
        task.started_at = datetime.now(UTC)
        task.progress = 0
        db.commit()

        command = build_command(task, output_dir, db)
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env={**os.environ, "LC_ALL": "C.UTF-8"},
        )
        redis.set(f"task:{task.task_id}:pid", str(process.pid), ex=settings.task_timeout_seconds + 300)
        threading.Thread(target=watch_cancel, args=(redis, task.task_id, process), daemon=True).start()

        assert process.stdout is not None
        for line in process.stdout:
            if redis.get(f"task:{task.task_id}:cancel"):
                mark_cancelled(db, task)
                return
            update_progress(db, redis, task, line)

        return_code = process.wait(timeout=10)
        if redis.get(f"task:{task.task_id}:cancel"):
            mark_cancelled(db, task)
            return
        if return_code != 0:
            raise RuntimeError(f"yt-dlp exited with code {return_code}")

        file_path = pick_downloaded_file(output_dir)
        if not file_path:
            raise RuntimeError("Download finished but no output file was found")
        mark_task_completed(db, task, file_path, file_path.stat().st_size)
        redis.set(f"task:{task.task_id}:progress", "100", ex=3600)
        db.commit()
    except Exception as exc:
        if redis.get(f"task:{task.task_id}:cancel"):
            mark_cancelled(db, task)
            return
        task.status = TaskStatus.FAILED
        task.error_message = str(exc)[:2000]
        task.completed_at = datetime.now(UTC)
        task.user.failed_tasks += 1
        db.commit()
        raise
    finally:
        redis.delete(f"task:{task.task_id}:pid")
        db.close()
        redis.close()


def build_command(task: DownloadTask, output_dir: Path, db) -> list[str]:
    limit_rate = _setting(db, "limit_rate", settings.default_limit_rate)
    max_filesize = get_int_setting(db, "vip_max_filesize_mb" if task.user.role == "vip" else "user_max_filesize_mb", settings.default_max_filesize_mb)
    output_template = str(output_dir / "%(title).150B-%(id)s.%(ext)s")
    common = [
        "yt-dlp",
        "--newline",
        "--no-playlist",
        "--restrict-filenames",
        "--limit-rate",
        limit_rate,
        "--max-filesize",
        f"{max_filesize}M",
        "-o",
        output_template,
    ]
    if task.task_type == TaskType.AUDIO:
        return [*common, "-x", "--audio-format", "mp3", "--audio-quality", "0", task.url]
    if task.task_type == TaskType.THUMBNAIL:
        return [*common, "--write-thumbnail", "--skip-download", task.url]
    if task.task_type == TaskType.SUBTITLE:
        return [*common, "--write-subs", "--write-auto-subs", "--skip-download", task.url]
    return [*common, "--merge-output-format", "mp4", "--concurrent-fragments", "4", "-f", task.quality or "bv*+ba/b", task.url]


def update_progress(db, redis: Redis, task: DownloadTask, line: str) -> None:
    match = PROGRESS_RE.search(line)
    if match:
        task.progress = float(match.group(1))
        redis.set(f"task:{task.task_id}:progress", str(task.progress), ex=3600)
    lower = line.lower()
    if "merging formats" in lower:
        task.status = TaskStatus.MERGING
    elif "destination" in lower and not task.title:
        task.title = line.split("Destination:", 1)[-1].strip()[-500:]
    elif "deleting original file" in lower or "converting video" in lower:
        task.status = TaskStatus.TRANSCODING
    db.commit()


def pick_downloaded_file(output_dir: Path) -> Path | None:
    files = [item for item in output_dir.rglob("*") if item.is_file() and not item.name.endswith(".part")]
    if not files:
        return None
    return max(files, key=lambda item: item.stat().st_mtime)


def watch_cancel(redis: Redis, task_id: str, process: subprocess.Popen) -> None:
    while process.poll() is None:
        if redis.get(f"task:{task_id}:cancel"):
            terminate_process(process)
            return
        time.sleep(0.5)


def terminate_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=8)


def mark_cancelled(db, task: DownloadTask) -> None:
    now = datetime.now(UTC)
    task.status = TaskStatus.CANCELLED
    task.cancelled_at = task.cancelled_at or now
    task.completed_at = task.completed_at or now
    db.commit()


def _setting(db, key: str, default: str) -> str:
    from app.services.settings import get_setting

    return get_setting(db, key, default) or default
