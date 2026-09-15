# Ganymede API — Role-Based Access Control

from enum import Enum
from typing import Optional
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User, Matter, MatterMembership


class Role(str, Enum):
    ADMINISTRATOR = "administrator"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    REVIEWER = "reviewer"
    IT_OPERATOR = "it_operator"


# Role hierarchy (higher = more privilege)
ROLE_HIERARCHY = {
    Role.ADMINISTRATOR: 100,
    Role.ATTORNEY: 80,
    Role.REVIEWER: 60,
    Role.PARALEGAL: 40,
    Role.IT_OPERATOR: 20,
}

# Permissions by role
ROLE_PERMISSIONS = {
    Role.ADMINISTRATOR: {
        "matter.create", "matter.read", "matter.delete",
        "user.create", "user.read", "user.delete",
        "document.upload", "document.read", "document.delete",
        "query.submit", "citation.view", "citation.feedback",
        "artifact.export", "audit.read",
    },
    Role.ATTORNEY: {
        "matter.create", "matter.read",
        "document.upload", "document.read",
        "query.submit", "citation.view", "citation.feedback",
        "artifact.export",
    },
    Role.REVIEWER: {
        "matter.read",
        "document.read",
        "query.submit", "citation.view", "citation.feedback",
        "artifact.export",
    },
    Role.PARALEGAL: {
        "matter.read",
        "document.read",
        "query.submit", "citation.view", "citation.feedback",
    },
    Role.IT_OPERATOR: {
        "matter.read",
        "document.read",
        "audit.read",
    },
}


def has_permission(user_role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    try:
        role = Role(user_role)
        return permission in ROLE_PERMISSIONS.get(role, set())
    except ValueError:
        return False


def require_permission(permission: str):
    """Dependency that requires a specific permission."""
    def checker(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission} required"
            )
        return current_user
    return checker


def get_matter_role(user: User, matter_id: str, db: Session) -> Optional[str]:
    """Get user's role for a specific matter, or None if not a member."""
    membership = db.query(MatterMembership).filter(
        MatterMembership.user_id == user.id,
        MatterMembership.matter_id == matter_id,
    ).first()
    if membership:
        return membership.role
    return None


def can_access_matter(user: User, matter_id: str, db: Session) -> bool:
    """Check if user has any access to a matter.
    
    Three tiers:
    1. Administrators: full access to all matters
    2. Matter members: access based on matter-level role
    3. Non-members: no access (even within same tenant)
    """
    if user.role == Role.ADMINISTRATOR:
        return True
    membership = db.query(MatterMembership).filter(
        MatterMembership.user_id == user.id,
        MatterMembership.matter_id == matter_id,
    ).first()
    return membership is not None


def require_matter_access(user: User, matter_id: str, db: Session):
    """Raise 403 if user cannot access matter."""
    if not can_access_matter(user, matter_id, db):
        raise HTTPException(status_code=403, detail="Access denied to this matter")


# Import here to avoid circular dependency
from app.core.deps import get_current_user
