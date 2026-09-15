# Ganymede API — Matter Membership Service

"""CRUD operations for matter-level membership management.

Matter membership grants users access to specific matters.
Combined with global RBAC (User.role → permissions), this provides
two-layer authorization:

1. Global: what actions can this role perform? (RBAC)
2. Matter: which matters can this user access? (membership)

Matter-level roles:
- lead: can manage members, edit/delete matter
- member: standard access (query, upload, etc.)
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Matter, User, MatterMembership


class MembershipError(Exception):
    """Raised when a membership operation fails."""
    def __init__(self, message: str, code: str = "membership_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def get_memberships(db: Session, matter_id: str) -> List[MatterMembership]:
    """List all memberships for a matter."""
    return db.query(MatterMembership).filter(
        MatterMembership.matter_id == matter_id
    ).all()


def get_user_memberships(db: Session, user_id: str) -> List[MatterMembership]:
    """List all matters a user is a member of."""
    return db.query(MatterMembership).filter(
        MatterMembership.user_id == user_id
    ).all()


def add_member(
    db: Session,
    matter_id: str,
    user_id: str,
    role: str = "member",
) -> MatterMembership:
    """Add a user to a matter.
    
    Args:
        db: database session
        matter_id: matter to add user to
        user_id: user to add
        role: matter-level role ("lead" or "member")
    
    Returns:
        The created MatterMembership
    
    Raises:
        MembershipError: if user/matter not found or already a member
    """
    if role not in ("lead", "member"):
        raise MembershipError(f"Invalid role: {role}. Must be 'lead' or 'member'.", "invalid_role")
    
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise MembershipError("Matter not found", "matter_not_found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise MembershipError("User not found", "user_not_found")
    
    existing = db.query(MatterMembership).filter(
        MatterMembership.matter_id == matter_id,
        MatterMembership.user_id == user_id,
    ).first()
    if existing:
        raise MembershipError("User is already a member of this matter", "already_member")
    
    membership = MatterMembership(
        id=uuid.uuid4(),
        matter_id=matter_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def remove_member(db: Session, matter_id: str, user_id: str):
    """Remove a user from a matter.
    
    Raises:
        MembershipError: if membership not found
    """
    membership = db.query(MatterMembership).filter(
        MatterMembership.matter_id == matter_id,
        MatterMembership.user_id == user_id,
    ).first()
    if not membership:
        raise MembershipError("User is not a member of this matter", "not_member")
    
    db.delete(membership)
    db.commit()


def update_member_role(db: Session, matter_id: str, user_id: str, role: str) -> MatterMembership:
    """Update a member's matter-level role.
    
    Raises:
        MembershipError: if membership not found or invalid role
    """
    if role not in ("lead", "member"):
        raise MembershipError(f"Invalid role: {role}. Must be 'lead' or 'member'.", "invalid_role")
    
    membership = db.query(MatterMembership).filter(
        MatterMembership.matter_id == matter_id,
        MatterMembership.user_id == user_id,
    ).first()
    if not membership:
        raise MembershipError("User is not a member of this matter", "not_member")
    
    membership.role = role
    db.commit()
    db.refresh(membership)
    return membership


def is_matter_lead(db: Session, user_id: str, matter_id: str) -> bool:
    """Check if a user is the lead of a matter."""
    membership = db.query(MatterMembership).filter(
        MatterMembership.matter_id == matter_id,
        MatterMembership.user_id == user_id,
        MatterMembership.role == "lead",
    ).first()
    return membership is not None
