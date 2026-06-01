from datetime import UTC, datetime
from ipaddress import ip_address, ip_network

from fastapi import HTTPException, status
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.all_models import IPBlacklist


def check_ip_blacklist(db: Session, client_ip: str | None) -> None:
    if not client_ip:
        return
    now = datetime.now(UTC)
    records = db.query(IPBlacklist).filter(IPBlacklist.status == "active").all()
    for record in records:
        if record.expired_at and record.expired_at < now:
            continue
        try:
            if record.ip and ip_address(client_ip) == ip_address(record.ip):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="IP is blacklisted")
            if record.cidr and ip_address(client_ip) in ip_network(record.cidr, strict=False):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="IP range is blacklisted")
        except ValueError:
            continue


def enforce_ip_hourly_limit(redis: Redis, client_ip: str | None) -> None:
    if not client_ip:
        return
    key = f"rate:tasks:{client_ip}:{datetime.now(UTC).strftime('%Y%m%d%H')}"
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, 3700)
    if count > settings.ip_hourly_limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many task submissions from this IP")
