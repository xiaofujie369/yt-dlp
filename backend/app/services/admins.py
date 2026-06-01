from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import UserRole, UserStatus
from app.models.all_models import User
from app.services.user_permissions import apply_role_template


def parse_admin_emails(raw: str | None = None) -> set[str]:
    value = settings.admin_emails if raw is None else raw
    return {email.strip().lower() for email in value.split(",") if email.strip()}


def promote_admin_emails(db: Session) -> int:
    admin_emails = parse_admin_emails()
    if not admin_emails:
        return 0

    users = db.query(User).filter(func.lower(User.email).in_(admin_emails)).all()
    changed = 0
    for user in users:
        if user.role != UserRole.ADMIN or user.status != UserStatus.ACTIVE:
            user.role = UserRole.ADMIN
            user.status = UserStatus.ACTIVE
            apply_role_template(user)
            changed += 1
    if changed:
        db.commit()
    return changed


def make_admin_by_email(db: Session, email: str, username: str | None = None) -> User:
    normalized_email = email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not user:
        user = User(
            koyun_user_id=f"email:{normalized_email}",
            email=normalized_email,
            username=username or normalized_email.split("@", 1)[0],
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        apply_role_template(user)
        db.add(user)
        db.flush()
    else:
        user.role = UserRole.ADMIN
        user.status = UserStatus.ACTIVE
        apply_role_template(user)
        if username:
            user.username = username
    db.commit()
    db.refresh(user)
    return user
