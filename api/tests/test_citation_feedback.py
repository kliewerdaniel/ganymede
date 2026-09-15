"""Tests for citation feedback feature."""

import pytest
from app.models import CitationFeedback, Artifact
from app.services.artifacts import (
    submit_citation_feedback, get_citation_feedback, ArtifactError,
)
import uuid


class TestCitationFeedback:
    """Test citation feedback submission and retrieval."""

    def test_submit_feedback_creates_record(self, db, attorney_user, test_matter):
        """Submitting feedback creates a CitationFeedback record."""
        artifact = Artifact(
            id=uuid.uuid4(),
            matter_id=test_matter.id,
            artifact_type="memo",
            title="Test",
            status="draft",
            content={},
            created_by=attorney_user.id,
        )
        db.add(artifact)
        db.flush()

        fb = submit_citation_feedback(
            db, str(artifact.id), attorney_user,
            citation_document_id=str(uuid.uuid4()),
            citation_page=1,
            citation_sha256="abc123",
            feedback="supporting",
        )

        assert fb.artifact_id == artifact.id
        assert fb.feedback == "supporting"
        assert fb.provided_by == attorney_user.id

    def test_get_feedback_for_artifact(self, db, attorney_user, test_matter):
        """Retrieve all feedback for an artifact."""
        artifact = Artifact(
            id=uuid.uuid4(),
            matter_id=test_matter.id,
            artifact_type="memo",
            title="Test",
            status="draft",
            content={},
            created_by=attorney_user.id,
        )
        db.add(artifact)
        db.flush()

        # Submit multiple feedback entries
        submit_citation_feedback(
            db, str(artifact.id), attorney_user,
            citation_document_id=str(uuid.uuid4()),
            citation_page=1, citation_sha256="aaa", feedback="supporting",
        )
        submit_citation_feedback(
            db, str(artifact.id), attorney_user,
            citation_document_id=str(uuid.uuid4()),
            citation_page=2, citation_sha256="bbb", feedback="wrong",
        )

        feedback = get_citation_feedback(db, str(artifact.id), attorney_user)
        assert len(feedback) == 2

    def test_invalid_feedback_rejected(self, db, attorney_user, test_matter):
        """Invalid feedback values are rejected."""
        artifact = Artifact(
            id=uuid.uuid4(),
            matter_id=test_matter.id,
            artifact_type="memo",
            title="Test",
            status="draft",
            content={},
            created_by=attorney_user.id,
        )
        db.add(artifact)
        db.flush()

        with pytest.raises(ArtifactError):
            submit_citation_feedback(
                db, str(artifact.id), attorney_user,
                citation_document_id=str(uuid.uuid4()),
                citation_page=1, citation_sha256="xyz",
                feedback="invalid_value",
            )

    def test_update_existing_feedback(self, db, attorney_user, test_matter):
        """User can update their feedback on same citation."""
        artifact = Artifact(
            id=uuid.uuid4(),
            matter_id=test_matter.id,
            artifact_type="memo",
            title="Test",
            status="draft",
            content={},
            created_by=attorney_user.id,
        )
        db.add(artifact)
        db.flush()

        doc_id = str(uuid.uuid4())
        fb1 = submit_citation_feedback(
            db, str(artifact.id), attorney_user,
            citation_document_id=doc_id,
            citation_page=1, citation_sha256="same",
            feedback="supporting",
        )
        fb2 = submit_citation_feedback(
            db, str(artifact.id), attorney_user,
            citation_document_id=doc_id,
            citation_page=1, citation_sha256="same",
            feedback="wrong",
        )

        assert fb1.id == fb2.id
        assert fb2.feedback == "wrong"

    def test_all_feedback_values_work(self, db, attorney_user, test_matter):
        """All four feedback values are accepted."""
        artifact = Artifact(
            id=uuid.uuid4(),
            matter_id=test_matter.id,
            artifact_type="memo",
            title="Test",
            status="draft",
            content={},
            created_by=attorney_user.id,
        )
        db.add(artifact)
        db.flush()

        for fb_val in ["supporting", "weak", "wrong", "inaccessible"]:
            fb = submit_citation_feedback(
                db, str(artifact.id), attorney_user,
                citation_document_id=str(uuid.uuid4()),
                citation_page=1, citation_sha256=fb_val,
                feedback=fb_val,
            )
            assert fb.feedback == fb_val


class TestCitationFeedbackAPI:
    """Test citation feedback HTTP endpoints."""

    def test_submit_feedback_endpoint(self):
        """POST /artifacts/{id}/feedback works."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/artifacts/00000000-0000-0000-0000-000000000001/feedback",
                json={
                    "citation_document_id": "00000000-0000-0000-0000-000000000002",
                    "citation_page": 1,
                    "citation_sha256": "abc",
                    "feedback": "supporting",
                },
            )
            # Should return 401 without auth
            assert resp.status_code == 401

    def test_get_feedback_endpoint(self):
        """GET /artifacts/{id}/feedback works."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        with TestClient(app) as client:
            resp = client.get(
                "/api/v1/artifacts/00000000-0000-0000-0000-000000000001/feedback",
            )
            # Should return 401 without auth
            assert resp.status_code == 401
