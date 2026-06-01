from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import UserRole, UserStatus
from app.models.all_models import User
from app.utils.security import decode_access_token


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    payload = decode_access_token(authorization.split(" ", 1)[1])
    user_id = payload.get("sub")
    user = db.get(User, int(user_id)) if user_id else None
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user
