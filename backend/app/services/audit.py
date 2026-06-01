from sqlalchemy.orm import Session

from app.models.all_models import OperationLog, User


def log_admin_action(
    db: Session,
    admin: User,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    db.add(
        OperationLog(
            admin_user_id=admin.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip=ip,
            user_agent=user_agent,
        )
    )
