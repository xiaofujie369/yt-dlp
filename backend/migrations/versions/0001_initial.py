"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def utc_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("koyun_user_id", sa.String(128), unique=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("username", sa.String(120), nullable=False),
        sa.Column("avatar", sa.String(500), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("daily_quota", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("used_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        *utc_columns(),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "download_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.String(64), unique=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(120), nullable=True),
        sa.Column("task_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("filename", sa.String(500), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("format", sa.String(120), nullable=True),
        sa.Column("quality", sa.String(80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("client_ip", sa.String(80), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        *utc_columns(),
    )
    op.create_index("ix_download_tasks_user_status", "download_tasks", ["user_id", "status"])
    op.create_index("ix_download_tasks_created_at", "download_tasks", ["created_at"])

    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("download_tasks.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("mime_type", sa.String(120), nullable=True),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        *utc_columns(),
    )

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(120), unique=True, nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("type", sa.String(30), nullable=False, server_default="string"),
        sa.Column("description", sa.String(500), nullable=True),
        *utc_columns(),
    )

    op.create_table(
        "domain_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("rule_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("remark", sa.String(500), nullable=True),
        *utc_columns(),
    )
    op.create_index("ix_domain_rules_domain_type", "domain_rules", ["domain", "rule_type"], unique=True)

    op.create_table(
        "ip_blacklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ip", sa.String(80), nullable=True),
        sa.Column("cidr", sa.String(80), nullable=True),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        *utc_columns(),
    )

    op.create_table(
        "operation_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("target_type", sa.String(80), nullable=True),
        sa.Column("target_id", sa.String(80), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip", sa.String(80), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "daily_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.Date(), unique=True, nullable=False),
        sa.Column("total_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_users", sa.Integer(), nullable=False, server_default="0"),
        *utc_columns(),
    )


def downgrade() -> None:
    op.drop_table("daily_stats")
    op.drop_table("operation_logs")
    op.drop_table("ip_blacklist")
    op.drop_index("ix_domain_rules_domain_type", table_name="domain_rules")
    op.drop_table("domain_rules")
    op.drop_table("system_settings")
    op.drop_table("files")
    op.drop_index("ix_download_tasks_created_at", table_name="download_tasks")
    op.drop_index("ix_download_tasks_user_status", table_name="download_tasks")
    op.drop_table("download_tasks")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
