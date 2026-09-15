# Ganymede API — Audit Log Service

import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import AuditLog

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    tenant_id: str,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> AuditLog:
    """Log an action to the audit log.

    Actions:
        auth.login, auth.logout, auth.register,
        query.submit, citation.view, citation.feedback,
        artifact.export, document.upload,
        matter.create, matter.access
    """
    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=metadata,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def query_audit_log(
    db: Session,
    tenant_id: str,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Query audit log entries with pagination."""
    query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    total = query.count()
    entries = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
    return entries, total
