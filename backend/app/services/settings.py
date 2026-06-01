from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.all_models import DomainRule, SystemSetting


DEFAULT_SETTINGS: dict[str, tuple[str, str, str]] = {
    "user_daily_quota": ("5", "int", "普通用户每日下载次数"),
    "vip_daily_quota": ("50", "int", "VIP 每日下载次数"),
    "user_max_filesize_mb": (str(settings.default_max_filesize_mb), "int", "普通用户最大文件 MB"),
    "vip_max_filesize_mb": (str(settings.vip_max_filesize_mb), "int", "VIP 最大文件 MB"),
    "user_retention_hours": ("6", "int", "普通用户文件保留小时数"),
    "vip_retention_hours": ("24", "int", "VIP 文件保留小时数"),
    "max_concurrent_tasks_per_user": ("2", "int", "单用户同时排队/下载任务数量"),
    "task_timeout_seconds": (str(settings.task_timeout_seconds), "int", "单任务超时秒数"),
    "limit_rate": (settings.default_limit_rate, "string", "yt-dlp 下载限速"),
    "allow_mp3": ("true", "bool", "是否允许 MP3"),
    "allow_subtitle": ("false", "bool", "是否允许字幕"),
    "allow_playlist": ("false", "bool", "是否允许播放列表"),
    "allow_guest": ("false", "bool", "是否允许游客访问"),
    "allow_registration": ("false", "bool", "是否开启注册"),
}

DEFAULT_ALLOWED_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "x.com",
    "twitter.com",
    "instagram.com",
    "bilibili.com",
]


def seed_defaults(db: Session) -> None:
    for key, (value, value_type, description) in DEFAULT_SETTINGS.items():
        exists = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not exists:
            db.add(SystemSetting(key=key, value=value, type=value_type, description=description))
    for domain in DEFAULT_ALLOWED_DOMAINS:
        exists = db.query(DomainRule).filter(DomainRule.domain == domain, DomainRule.rule_type == "allow").first()
        if not exists:
            db.add(DomainRule(domain=domain, rule_type="allow", status="active", remark="Default allowed platform"))
    db.commit()


def get_setting(db: Session, key: str, default: str | None = None) -> str | None:
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    return setting.value if setting else default


def get_int_setting(db: Session, key: str, default: int) -> int:
    value = get_setting(db, key, str(default))
    try:
        return int(value or default)
    except ValueError:
        return default


def get_bool_setting(db: Session, key: str, default: bool) -> bool:
    value = (get_setting(db, key, str(default)).lower() if get_setting(db, key, None) is not None else str(default).lower())
    return value in {"true", "1", "yes", "on"}
