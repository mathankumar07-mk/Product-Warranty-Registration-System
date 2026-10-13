"""Reconcile columns: add model columns missing from older databases.

Revision ID: 0003_reconcile_columns
Revises: 0002_extended_backend
Create Date: 2026-10-14

Idempotent: only adds columns/constraints the inspector reports as missing,
so it is a safe no-op on fresh databases. Server defaults are supplied for
NOT NULL columns landing on non-empty tables (products.warranty_available,
products.updated_at) and match the model-level defaults.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_reconcile_columns"
down_revision = "0002_extended_backend"
branch_labels = None
depends_on = None


def _addable_column(table_name: str, column: sa.Column) -> sa.Column:
    # NOTE: foreign keys are created explicitly in upgrade(), never inline,
    # so the constraint name is created exactly once.
    kwargs: dict = {"nullable": column.nullable}
    if column.server_default is not None:
        kwargs["server_default"] = column.server_default
    if (table_name, column.name) == ("products", "warranty_available"):
        kwargs["server_default"] = sa.false()
    elif (table_name, column.name) == ("products", "updated_at"):
        kwargs["server_default"] = sa.func.now()
    return sa.Column(column.name, column.type, **kwargs)


def _existing_fk_columns(inspector, table_name: str) -> set[str]:
    constrained: set[str] = set()
    for fk in inspector.get_foreign_keys(table_name):
        constrained.update(fk["constrained_columns"])
        if fk.get("name"):
            constrained.add(f"named:{fk['name']}")
    return constrained


def upgrade() -> None:
    from app.core.database import Base
    import app.models  # noqa: F401

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in Base.metadata.sorted_tables:
        if table.name == "alembic_version" or not inspector.has_table(table.name):
            continue
        existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
        existing_fks = _existing_fk_columns(inspector, table.name)
        for column in table.columns:
            added = False
            if column.name not in existing_cols:
                op.add_column(table.name, _addable_column(table.name, column))
                added = True
            if column.foreign_keys and column.name not in existing_fks:
                for fk in column.foreign_keys:
                    referred_table, _, referred_col = fk.target_fullname.partition(".")
                    op.create_foreign_key(
                        f"{table.name}_{column.name}_fkey",
                        table.name,
                        referred_table,
                        [column.name],
                        [referred_col],
                        ondelete=fk.ondelete,
                        onupdate=fk.onupdate,
                    )
            if added:
                existing_cols.add(column.name)


def downgrade() -> None:
    pass
