"""Baseline: ensure all metadata tables exist (idempotent).

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-13
"""
from __future__ import annotations

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Source of truth is app.models metadata; create_all is checkfirst-safe
    # so this works on fresh MySQL/Postgres/SQLite and is a no-op otherwise.
    from app.core.database import Base, engine
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def downgrade() -> None:
    pass
