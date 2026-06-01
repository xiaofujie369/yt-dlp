import argparse

from app.core.database import SessionLocal
from app.services.admins import make_admin_by_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote or create an administrator by email")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--username", default=None, help="Optional display name when creating a new user")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = make_admin_by_email(db, args.email, args.username)
        print(f"admin ready: id={user.id} email={user.email} role={user.role}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
