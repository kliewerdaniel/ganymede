"""Tests for matter membership service and endpoints."""

import pytest
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Matter, User, MatterMembership
from app.services.membership import (
    add_member, remove_member, get_memberships, get_user_memberships,
    update_member_role, is_matter_lead, MembershipError,
)
from app.core.rbac import can_access_matter
from app.core.auth import hash_password


@pytest.fixture
def attorney_user(db: Session) -> User:
    """Create an attorney user for testing."""
    # Clean up any existing test data
    db.query(MatterMembership).filter(
        MatterMembership.matter_id.in_([
            "22222222-2222-2222-2222-222222222222",
            "33333333-3333-3333-3333-333333333333",
        ])
    ).delete(synchronize_session=False)
    db.query(User).filter(User.id == "11111111-1111-1111-1111-111111111111").delete(synchronize_session=False)
    db.query(Matter).filter(Matter.id.in_([
        "22222222-2222-2222-2222-222222222222",
        "33333333-3333-3333-3333-333333333333",
    ])).delete(synchronize_session=False)
    db.commit()
    
    user = User(
        id="11111111-1111-1111-1111-111111111111",
        tenant_id="00000000-0000-0000-0000-000000000001",
        email="attorney@test.com",
        name="Test Attorney",
        role="attorney",
        password_hash=hash_password("password123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def matter_a(db: Session) -> Matter:
    """Create a test matter."""
    # Clean up memberships first
    db.query(MatterMembership).filter(
        MatterMembership.matter_id == "22222222-2222-2222-2222-222222222222"
    ).delete(synchronize_session=False)
    db.query(Matter).filter(Matter.id == "22222222-2222-2222-2222-222222222222").delete(synchronize_session=False)
    db.commit()
    
    matter = Matter(
        id="22222222-2222-2222-2222-222222222222",
        tenant_id="00000000-0000-0000-0000-000000000001",
        name="Test Matter A",
    )
    db.add(matter)
    db.commit()
    db.refresh(matter)
    return matter


@pytest.fixture
def matter_b(db: Session) -> Matter:
    """Create another test matter."""
    # Clean up memberships first
    db.query(MatterMembership).filter(
        MatterMembership.matter_id == "33333333-3333-3333-3333-333333333333"
    ).delete(synchronize_session=False)
    db.query(Matter).filter(Matter.id == "33333333-3333-3333-3333-333333333333").delete(synchronize_session=False)
    db.commit()
    
    matter = Matter(
        id="33333333-3333-3333-3333-333333333333",
        tenant_id="00000000-0000-0000-0000-000000000001",
        name="Test Matter B",
    )
    db.add(matter)
    db.commit()
    db.refresh(matter)
    return matter


class TestAddMember:
    def test_add_member_success(self, db, attorney_user, matter_a):
        """Adding a member creates a membership record."""
        m = add_member(db, str(matter_a.id), str(attorney_user.id), "lead")
        assert m.matter_id == matter_a.id
        assert m.user_id == attorney_user.id
        assert m.role == "lead"

    def test_add_duplicate_member_fails(self, db, attorney_user, matter_a):
        """Adding the same user twice raises error."""
        add_member(db, str(matter_a.id), str(attorney_user.id), "lead")
        with pytest.raises(MembershipError, match="already a member"):
            add_member(db, str(matter_a.id), str(attorney_user.id), "member")

    def test_add_member_invalid_role(self, db, attorney_user, matter_a):
        """Invalid role raises error."""
        with pytest.raises(MembershipError, match="Invalid role"):
            add_member(db, str(matter_a.id), str(attorney_user.id), "superadmin")

    def test_add_member_matter_not_found(self, db, attorney_user):
        """Adding to non-existent matter raises error."""
        with pytest.raises(MembershipError, match="Matter not found"):
            add_member(db, "99999999-9999-9999-9999-999999999999", str(attorney_user.id), "lead")

    def test_add_member_user_not_found(self, db, matter_a):
        """Adding non-existent user raises error."""
        with pytest.raises(MembershipError, match="User not found"):
            add_member(db, str(matter_a.id), "99999999-9999-9999-9999-999999999999", "lead")


class TestRemoveMember:
    def test_remove_member_success(self, db, attorney_user, matter_a):
        """Removing a member deletes the record."""
        add_member(db, str(matter_a.id), str(attorney_user.id), "lead")
        remove_member(db, str(matter_a.id), str(attorney_user.id))
        assert get_memberships(db, str(matter_a.id)) == []

    def test_remove_non_member_fails(self, db, attorney_user, matter_a):
        """Removing a user who is not a member raises error."""
        with pytest.raises(MembershipError, match="not a member"):
            remove_member(db, str(matter_a.id), str(attorney_user.id))


class TestGetMemberships:
    def test_get_memberships_empty(self, db, matter_a):
        """Empty list when no members."""
        assert get_memberships(db, str(matter_a.id)) == []

    def test_get_memberships_multiple(self, db, attorney_user, matter_a, matter_b):
        """Returns all members across matters."""
        add_member(db, str(matter_a.id), str(attorney_user.id), "lead")
        add_member(db, str(matter_b.id), str(attorney_user.id), "member")
        
        a_members = get_memberships(db, str(matter_a.id))
        b_members = get_memberships(db, str(matter_b.id))
        assert len(a_members) == 1
        assert len(b_members) == 1
        assert a_members[0].matter_id == matter_a.id
        assert b_members[0].matter_id == matter_b.id

    def test_get_user_memberships(self, db, attorney_user, matter_a, matter_b):
        """Returns all matters for a user."""
        add_member(db, str(matter_a.id), str(attorney_user.id), "lead")
        add_member(db, str(matter_b.id), str(attorney_user.id), "member")
        
        user_memberships = get_user_memberships(db, str(attorney_user.id))
        assert len(user_memberships) == 2


class TestUpdateMemberRole:
    def test_update_role_success(self, db, attorney_user, matter_a):
        """Changing role updates the record."""
        add_member(db, str(matter_a.id), str(attorney_user.id), "lead")
        m = update_member_role(db, str(matter_a.id), str(attorney_user.id), "member")
        assert m.role == "member"

    def test_update_role_not_a_member(self, db, attorney_user, matter_a):
        """Updating a non-member raises error."""
        with pytest.raises(MembershipError, match="not a member"):
            update_member_role(db, str(matter_a.id), str(attorney_user.id), "lead")


class TestIsMatterLead:
    def test_is_lead_true(self, db, attorney_user, matter_a):
        """Returns True for a lead."""
        add_member(db, str(matter_a.id), str(attorney_user.id), "lead")
        assert is_matter_lead(db, str(attorney_user.id), str(matter_a.id)) is True

    def test_is_lead_false_for_member(self, db, attorney_user, matter_a):
        """Returns False for non-lead member."""
        add_member(db, str(matter_a.id), str(attorney_user.id), "member")
        assert is_matter_lead(db, str(attorney_user.id), str(matter_a.id)) is False

    def test_is_lead_false_for_non_member(self, db, attorney_user, matter_a):
        """Returns False for non-member."""
        assert is_matter_lead(db, str(attorney_user.id), str(matter_a.id)) is False


class TestCanAccessMatter:
    def test_admin_access_all_matters(self, db, attorney_user, matter_a):
        """Administrators can access all matters."""
        attorney_user.role = "administrator"
        db.commit()
        assert can_access_matter(attorney_user, str(matter_a.id), db) is True

    def test_member_access_own_matter(self, db, attorney_user, matter_a):
        """Members can access their own matter."""
        add_member(db, str(matter_a.id), str(attorney_user.id), "lead")
        assert can_access_matter(attorney_user, str(matter_a.id), db) is True

    def test_non_member_no_access(self, db, attorney_user, matter_a):
        """Non-members cannot access the matter."""
        assert can_access_matter(attorney_user, str(matter_a.id), db) is False
