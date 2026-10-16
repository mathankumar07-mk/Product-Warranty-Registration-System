"""Immutable audit trail for admin actions."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_admin_action(
    db: Session,
    *,
    admin_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    details: str | None = None,
    commit: bool = True,
) -> AuditLog:
    entry = AuditLog(
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=details,
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    else:
        db.flush()
    return entry


def list_audit_logs(
    db: Session,
    *,
    action: str | None = None,
    entity_type: str | None = None,
    admin_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[AuditLog]:
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if admin_id is not None:
        query = query.filter(AuditLog.admin_id == admin_id)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return query.offset((page - 1) * page_size).limit(page_size).all()
