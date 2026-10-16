"""Admin is_active flag + audit_logs table.

Revision ID: 0006_admin_audit
Revises: 0005_relax_model_nullable
Create Date: 2026-10-16

Additive only; no data deleted.
- admins.is_active BOOLEAN NOT NULL DEFAULT TRUE (existing rows backfilled TRUE)
- audit_logs table (immutable admin action trail)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_admin_audit"
down_revision = "0005_relax_model_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("admins"):
        admin_cols = {c["name"] for c in inspector.get_columns("admins")}
        if "is_active" not in admin_cols:
            op.add_column("admins", sa.Column("is_active", sa.Boolean(), nullable=True))
            op.execute("UPDATE admins SET is_active = TRUE WHERE is_active IS NULL")
            if bind.dialect.name != "sqlite":
                op.alter_column("admins", "is_active", existing_type=sa.Boolean(), nullable=False)
            else:
                # SQLite: keep nullable in DDL; model default + app guard enforce True.
                pass

    if not inspector.has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
            sa.Column("admin_id", sa.Integer(), sa.ForeignKey("admins.id", ondelete="SET NULL"), nullable=True),
            sa.Column("action", sa.String(120), nullable=False),
            sa.Column("entity_type", sa.String(80), nullable=True),
            sa.Column("entity_id", sa.String(80), nullable=True),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_audit_logs_admin_id", "audit_logs", ["admin_id"])
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
        op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("audit_logs"):
        op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
        op.drop_index("ix_audit_logs_action", table_name="audit_logs")
        op.drop_index("ix_audit_logs_admin_id", table_name="audit_logs")
        op.drop_table("audit_logs")
    # Keep admins.is_active (data-preserving); downgrade is a no-op for it.
