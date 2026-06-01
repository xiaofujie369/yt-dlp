from datetime import UTC, datetime

from sqlalchemy import BigInteger, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    koyun_user_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    username: Mapped[str] = mapped_column(String(120))
    avatar: Mapped[str | None] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(20), default="user")
    status: Mapped[str] = mapped_column(String(20), default="active")
    daily_quota: Mapped[int] = mapped_column(Integer, default=5)
    used_today: Mapped[int] = mapped_column(Integer, default=0)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    success_tasks: Mapped[int] = mapped_column(Integer, default=0)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tasks: Mapped[list["DownloadTask"]] = relationship(back_populates="user")


class DownloadTask(Base, TimestampMixin):
    __tablename__ = "download_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    platform: Mapped[str | None] = mapped_column(String(120))
    task_type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    progress: Mapped[float] = mapped_column(Float, default=0)
    title: Mapped[str | None] = mapped_column(String(500))
    filename: Mapped[str | None] = mapped_column(String(500))
    file_path: Mapped[str | None] = mapped_column(String(1000))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    duration: Mapped[float | None] = mapped_column(Float)
    format: Mapped[str | None] = mapped_column(String(120))
    quality: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    client_ip: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="tasks")
    files: Mapped[list["DownloadFile"]] = relationship(back_populates="task")


class DownloadFile(Base, TimestampMixin):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("download_tasks.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(500))
    file_path: Mapped[str] = mapped_column(String(1000))
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    mime_type: Mapped[str | None] = mapped_column(String(120))
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    task: Mapped[DownloadTask] = relationship(back_populates="files")


class SystemSetting(Base, TimestampMixin):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(30), default="string")
    description: Mapped[str | None] = mapped_column(String(500))


class DomainRule(Base, TimestampMixin):
    __tablename__ = "domain_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    rule_type: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    remark: Mapped[str | None] = mapped_column(String(500))


class IPBlacklist(Base, TimestampMixin):
    __tablename__ = "ip_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip: Mapped[str | None] = mapped_column(String(80), index=True)
    cidr: Mapped[str | None] = mapped_column(String(80), index=True)
    reason: Mapped[str | None] = mapped_column(String(500))
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(120))
    target_type: Mapped[str | None] = mapped_column(String(80))
    target_id: Mapped[str | None] = mapped_column(String(80))
    detail: Mapped[str | None] = mapped_column(Text)
    ip: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DailyStat(Base, TimestampMixin):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date = mapped_column(Date, unique=True, index=True)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    success_tasks: Mapped[int] = mapped_column(Integer, default=0)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    total_file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
