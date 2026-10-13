"""Relax vestigial NOT NULL columns left by older schemas.

Revision ID: 0004_relax_vestigial_columns
Revises: 0003_reconcile_columns
Create Date: 2026-10-14

Older databases contain columns the models no longer use
(e.g. carts.updated_at, orders.address_id). Where such a column is
NOT NULL without a default, every INSERT omits it and fails on
PostgreSQL/MySQL. This migration drops the NOT NULL constraint on
those orphan columns only. Data is preserved; nothing is dropped.
Idempotent: skips columns already nullable.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_relax_vestigial_columns"
down_revision = "0003_reconcile_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.core.database import Base
    import app.models  # noqa: F401

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return  # SQLite is lax here and cannot ALTER COLUMN; tests recreate schema.
    inspector = sa.inspect(bind)
    for table in Base.metadata.sorted_tables:
        if table.name == "alembic_version" or not inspector.has_table(table.name):
            continue
        model_cols = set(table.columns.keys())
        for col in inspector.get_columns(table.name):
            if col["name"] in model_cols:
                continue
            if col["nullable"] or col.get("default"):
                continue
            op.alter_column(
                table.name,
                col["name"],
                existing_type=col["type"],
                nullable=True,
            )


def downgrade() -> None:
    pass
