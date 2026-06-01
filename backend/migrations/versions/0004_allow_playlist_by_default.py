"""allow playlist by default for existing users

Revision ID: 0004_allow_playlist_by_default
Revises: 0003_user_permission_fields
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_allow_playlist_by_default"
down_revision = "0003_user_permission_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "allow_playlist", server_default=sa.true())
    op.execute("UPDATE users SET allow_playlist = true WHERE allow_playlist = false")


def downgrade() -> None:
    op.alter_column("users", "allow_playlist", server_default=sa.false())
