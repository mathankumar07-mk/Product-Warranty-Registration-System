"""Relax NOT NULL where the model declares a column nullable.

Revision ID: 0005_relax_model_nullable
Revises: 0004_relax_vestigial_columns
Create Date: 2026-10-14

Older databases mark some columns NOT NULL that current models declare
nullable (e.g. payments.transaction_id, set only after gateway processing).
INSERTs omitting them fail on PostgreSQL/MySQL. This aligns nullability
with the models. Data preserved; idempotent.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_relax_model_nullable"
down_revision = "0004_relax_vestigial_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.core.database import Base
    import app.models  # noqa: F401

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return  # lax here; tests recreate schema.
    inspector = sa.inspect(bind)
    for table in Base.metadata.sorted_tables:
        if table.name == "alembic_version" or not inspector.has_table(table.name):
            continue
        db_cols = {c["name"]: c for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if not column.nullable or column.primary_key:
                continue
            current = db_cols.get(column.name)
            if not current or current["nullable"] or current.get("default"):
                continue
            op.alter_column(
                table.name,
                column.name,
                existing_type=current["type"],
                nullable=True,
            )


def downgrade() -> None:
    pass
