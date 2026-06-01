from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(subject: str, role: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expires_minutes)
    payload = {"sub": subject, "role": role, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc
