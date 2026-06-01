from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_url: str = "http://localhost:3100"
    database_url: str = "postgresql+psycopg://koyun_ytdlp:change_me@localhost:5432/koyun_ytdlp"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change_me_long_random_string"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 10080
    admin_emails: str = "4869150@qq.com"

    koyun_oauth_client_id: str = ""
    koyun_oauth_client_secret: str = ""
    koyun_oauth_authorize_url: str = ""
    koyun_oauth_token_url: str = ""
    koyun_oauth_userinfo_url: str = ""
    koyun_oauth_redirect_uri: str = "http://localhost:8100/api/auth/callback"

    download_dir: str = "/data/downloads"
    max_workers: int = 2
    default_limit_rate: str = "5M"
    default_max_filesize_mb: int = 512
    vip_max_filesize_mb: int = 2048
    task_timeout_seconds: int = 3600
    ip_hourly_limit: int = 20

    default_user_quota: int = 5
    vip_user_quota: int = 50
    default_retention_hours: int = 6
    vip_retention_hours: int = 24

    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3100"])


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
