"""add user permission fields

Revision ID: 0003_user_permission_fields
Revises: 0002_add_cancelled_at
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_user_permission_fields"
down_revision = "0002_add_cancelled_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("max_concurrent_tasks", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("users", sa.Column("max_file_size_mb", sa.Integer(), nullable=False, server_default="500"))
    op.add_column("users", sa.Column("max_duration_minutes", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("users", sa.Column("file_retention_hours", sa.Integer(), nullable=False, server_default="24"))
    op.add_column("users", sa.Column("allow_video", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("allow_audio", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("allow_thumbnail", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("allow_subtitle", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("allow_playlist", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("allow_batch", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("allowed_platforms", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("denied_platforms", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("remark", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("banned_reason", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("banned_until", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        """
        UPDATE users
        SET
            daily_quota = 50,
            max_concurrent_tasks = 3,
            max_file_size_mb = 2048,
            max_duration_minutes = 180,
            file_retention_hours = 72,
            allow_playlist = true,
            allow_batch = true
        WHERE role = 'vip'
        """
    )
    op.execute(
        """
        UPDATE users
        SET
            daily_quota = 999,
            max_concurrent_tasks = 10,
            max_file_size_mb = 10240,
            max_duration_minutes = 720,
            file_retention_hours = 168,
            allow_playlist = true,
            allow_batch = true
        WHERE role = 'admin'
        """
    )


def downgrade() -> None:
    op.drop_column("users", "banned_until")
    op.drop_column("users", "banned_reason")
    op.drop_column("users", "remark")
    op.drop_column("users", "denied_platforms")
    op.drop_column("users", "allowed_platforms")
    op.drop_column("users", "allow_batch")
    op.drop_column("users", "allow_playlist")
    op.drop_column("users", "allow_subtitle")
    op.drop_column("users", "allow_thumbnail")
    op.drop_column("users", "allow_audio")
    op.drop_column("users", "allow_video")
    op.drop_column("users", "file_retention_hours")
    op.drop_column("users", "max_duration_minutes")
    op.drop_column("users", "max_file_size_mb")
    op.drop_column("users", "max_concurrent_tasks")
