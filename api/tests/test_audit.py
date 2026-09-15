# Ganymede API — Audit Log Tests

import os
import sys
import uuid
import pytest
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import get_settings
from app.core.audit import AuditLog, log_action, query_audit_log
from app.models import Base, Tenant, User

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def tenant_id(db):
    tenant = db.query(Tenant).first()
    if tenant:
        return str(tenant.id)
    # Create test tenant
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return str(tenant.id)


@pytest.fixture
def user_id(db, tenant_id):
    """Create a real user and return its ID."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=f"test-{uuid.uuid4().hex[:8]}@test.com",
        name="Test User",
        password_hash="$2b$12$dummyhash",
        role="attorney",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return str(user.id)


@pytest.fixture(autouse=True)
def clean_audit_logs(db):
    """Clean up audit logs before and after each test."""
    db.execute(text("DELETE FROM audit_logs"))
    db.commit()
    yield
    db.execute(text("DELETE FROM audit_logs"))
    db.commit()


class TestAuditLog:
    def test_create_audit_entry(self, db, tenant_id, user_id):
        entry = log_action(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="auth.login",
            resource_type="session",
            resource_id="test-session-123",
            metadata={"ip": "127.0.0.1"},
        )
        assert entry.id is not None
        assert entry.action == "auth.login"
        assert entry.resource_type == "session"
        assert entry.resource_id == "test-session-123"
        assert entry.metadata_json == {"ip": "127.0.0.1"}
        assert entry.created_at is not None

    def test_log_query_submit(self, db, tenant_id, user_id):
        entry = log_action(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="query.submit",
            resource_type="matter",
            resource_id="matter-123",
            metadata={"query": "test question", "result_count": 5},
        )
        assert entry.action == "query.submit"
        assert entry.metadata_json["query"] == "test question"

    def test_log_citation_feedback(self, db, tenant_id, user_id):
        entry = log_action(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="citation.feedback",
            resource_type="citation",
            resource_id="citation-456",
            metadata={"feedback": "supporting"},
        )
        assert entry.action == "citation.feedback"
        assert entry.metadata_json["feedback"] == "supporting"

    def test_query_audit_log_by_user(self, db, tenant_id, user_id):
        # Create entries
        for i in range(3):
            log_action(db, tenant_id, user_id, "query.submit", "matter", f"matter-{i}")

        entries, total = query_audit_log(db, tenant_id, user_id=user_id)
        assert total == 3
        assert len(entries) == 3

    def test_query_audit_log_by_action(self, db, tenant_id, user_id):
        log_action(db, tenant_id, user_id, "auth.login", "session")
        log_action(db, tenant_id, user_id, "query.submit", "matter")

        entries, total = query_audit_log(db, tenant_id, action="auth.login")
        assert total == 1
        assert entries[0].action == "auth.login"

    def test_query_audit_log_pagination(self, db, tenant_id, user_id):
        for i in range(5):
            log_action(db, tenant_id, user_id, "query.submit", "matter", f"m-{i}")

        entries, total = query_audit_log(db, tenant_id, limit=2, offset=0)
        assert total == 5
        assert len(entries) == 2

    def test_query_audit_log_empty(self, db, tenant_id):
        entries, total = query_audit_log(db, tenant_id, action="nonexistent")
        assert total == 0
        assert len(entries) == 0

    def test_audit_log_ordered_by_created_at_desc(self, db, tenant_id, user_id):
        log_action(db, tenant_id, user_id, "auth.login", "session")
        log_action(db, tenant_id, user_id, "query.submit", "matter")

        entries, total = query_audit_log(db, tenant_id, user_id=user_id)
        assert total == 2
        # First entry should be most recent (query.submit)
        assert entries[0].action == "query.submit"
