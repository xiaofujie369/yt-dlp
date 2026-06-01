from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import FileResponse
from redis import Redis
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.all_models import User
from app.schemas.common import Page
from app.schemas.tasks import FileOut, TaskCreate, TaskCreated, TaskOut
from app.services.rate_limit import check_ip_blacklist, enforce_ip_hourly_limit
from app.services.tasks import cancel_task, create_task, get_download_file, get_user_task, list_user_tasks, soft_delete_task

router = APIRouter(tags=["tasks"])


@router.post("/tasks", response_model=TaskCreated, status_code=202)
def create_download_task(
    payload: TaskCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)],
    user_agent: Annotated[str | None, Header()] = None,
) -> TaskCreated:
    client_ip = request.client.host if request.client else None
    check_ip_blacklist(db, client_ip)
    enforce_ip_hourly_limit(redis, client_ip)
    task = create_task(db, redis, user, payload, client_ip, user_agent)
    return TaskCreated(task_id=task.task_id, status=task.status)


@router.get("/tasks", response_model=Page[TaskOut])
def my_tasks(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page[TaskOut]:
    items, total = list_user_tasks(db, user, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def task_detail(task_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]):
    return get_user_task(db, user, task_id)


@router.get("/tasks/{task_id}/files", response_model=list[FileOut])
def task_files(task_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]):
    task = get_user_task(db, user, task_id)
    return [file for file in task.files if file.status == "active"]


@router.post("/tasks/{task_id}/cancel", response_model=TaskOut)
def cancel_user_task(
    task_id: str,
    db: Annotated[Session, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)],
):
    return cancel_task(db, redis, get_user_task(db, user, task_id))


@router.delete("/tasks/{task_id}", status_code=204)
def delete_user_task(task_id: str, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]):
    soft_delete_task(db, get_user_task(db, user, task_id))


@router.get("/files/{file_id}/download")
def download_file(file_id: int, db: Annotated[Session, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]):
    file = get_download_file(db, user, file_id)
    return FileResponse(file.file_path, filename=file.filename, media_type=file.mime_type or "application/octet-stream")
