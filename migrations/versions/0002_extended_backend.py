"""Extended backend: refresh tokens, order/warranty numbers, category policies.

Revision ID: 0002_extended_backend
Revises: 0001_baseline
Create Date: 2026-10-14

Idempotent: every step checks the inspector first, so fresh databases
(where baseline create_all already added everything) are a safe no-op.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_extended_backend"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _add_column(table: str, column: sa.Column) -> None:
    if column.name not in _columns(table):
        op.add_column(table, column)


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "refresh_tokens" not in inspector.get_table_names():
        op.create_table(
            "refresh_tokens",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("jti", sa.String(64), nullable=False, unique=True, index=True),
            sa.Column("subject", sa.String(64), nullable=False, index=True),
            sa.Column("is_admin", sa.Boolean(), nullable=False, default=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked", sa.Boolean(), nullable=False, default=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    _add_column("orders", sa.Column("order_number", sa.String(32), nullable=True))
    _add_column("orders", sa.Column("idempotency_key", sa.String(64), nullable=True))
    _add_column("payments", sa.Column("idempotency_key", sa.String(64), nullable=True))
    _add_column("warranty_policies", sa.Column("category_id", sa.Integer(), nullable=True))
    _add_column(
        "warranty_policies",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    _add_column("warranty_policies", sa.Column("updated_at", sa.DateTime(), nullable=True))
    _add_column("warranty_registrations", sa.Column("warranty_number", sa.String(32), nullable=True))
    _add_column("warranty_registrations", sa.Column("proof_reference", sa.String(255), nullable=True))
    # Existing warranty_policies.product_id becomes nullable (category policies).
    cols = {c["name"]: c for c in sa.inspect(op.get_bind()).get_columns("warranty_policies")}
    if "product_id" in cols and not cols["product_id"]["nullable"]:
        op.alter_column("warranty_policies", "product_id", existing_type=sa.Integer(), nullable=True)
    # Extend warranty_status enum with PENDING_REVIEW on MySQL/Postgres only.
    dialect = op.get_bind().dialect.name
    if dialect == "mysql":
        op.execute(
            "ALTER TABLE warranty_registrations MODIFY COLUMN warranty_status "
            "ENUM('PENDING','PENDING_REVIEW','ACTIVE','EXPIRED','CANCELLED') NOT NULL"
        )
    elif dialect == "postgresql":
        op.execute("ALTER TYPE \"warrantystatus\" ADD VALUE IF NOT EXISTS 'PENDING_REVIEW'")


def downgrade() -> None:
    pass
