# Ganymede API — Pytest Configuration and Fixtures

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import get_settings
from app.models import Base, User, Matter, MatterMembership
from app.core.auth import hash_password
import uuid

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create a fresh database session for a test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def attorney_user(db) -> User:
    """Get an attorney user from the database."""
    user = db.query(User).filter(User.role == "attorney").first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            tenant_id="00000000-0000-0000-0000-000000000001",
            email=f"attorney-{uuid.uuid4().hex[:6]}@law.com",
            name="Test Attorney",
            role="attorney",
            password_hash=hash_password("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def test_matter(db, attorney_user) -> Matter:
    """Get a test matter where attorney is lead."""
    matter = db.query(Matter).first()
    if not matter:
        matter = Matter(
            id=uuid.uuid4(),
            tenant_id="00000000-0000-0000-0000-000000000001",
            name="Test Matter",
        )
        db.add(matter)
        db.commit()
        db.refresh(matter)

    # Ensure attorney is lead
    membership = db.query(MatterMembership).filter(
        MatterMembership.matter_id == matter.id,
        MatterMembership.user_id == attorney_user.id,
    ).first()
    if not membership:
        membership = MatterMembership(
            matter_id=matter.id,
            user_id=attorney_user.id,
            role="lead",
        )
        db.add(membership)
        db.commit()

    return matter
