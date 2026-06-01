import argparse
from datetime import UTC, datetime

from app.core.database import SessionLocal
from app.core.enums import UserRole
from app.models.all_models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or promote a Koyun admin user")
    parser.add_argument("--koyun-user-id", required=True)
    parser.add_argument("--email", default=None)
    parser.add_argument("--username", default="Admin")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.koyun_user_id == args.koyun_user_id).first()
        if not user:
            user = User(
                koyun_user_id=args.koyun_user_id,
                email=args.email,
                username=args.username,
                role=UserRole.ADMIN,
                daily_quota=9999,
                last_login_at=datetime.now(UTC),
            )
            db.add(user)
        else:
            user.role = UserRole.ADMIN
            user.status = "active"
        db.commit()
        print(f"admin ready: id={user.id} koyun_user_id={user.koyun_user_id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
