"""Tests for artifact services: chronology, issue table, memo, approval workflow."""

import pytest
from unittest.mock import MagicMock
from app.models import Artifact
from app.services.artifacts import (
    generate_chronology, generate_issue_table, generate_memo,
    get_artifact, list_artifacts, update_artifact_content,
    submit_for_review, approve_artifact, reject_artifact,
    get_artifact_versions, get_approval_history,
    ArtifactError,
)
import uuid


def _make_mock_citation(doc_id=None, page=1, text="Test passage"):
    """Create a mock citation object."""
    return MagicMock(
        document_id=doc_id or uuid.uuid4(),
        page=page,
        start_offset=0,
        end_offset=len(text),
        quoted_text=text,
        sha256="abc123",
    )


class TestArtifactService:
    """Test artifact CRUD and workflow."""

    def test_generate_chronology_creates_artifact(self, db, attorney_user, test_matter):
        """Chronology generation creates artifact with events."""
        mock_citations = [_make_mock_citation()]

        def fake_retrieve(db, matter_id, query, top_k=10):
            return mock_citations

        artifact = generate_chronology(
            db, str(test_matter.id), attorney_user,
            query_text="timeline", top_k=5,
            retriever=fake_retrieve,
        )
        assert artifact.artifact_type == "chronology"
        assert artifact.status == "draft"
        assert artifact.content is not None
        assert "events" in artifact.content

    def test_generate_issue_table_creates_artifact(self, db, attorney_user, test_matter):
        """Issue table generation creates artifact with issues."""
        mock_citations = [_make_mock_citation()]

        def fake_retrieve(db, matter_id, query, top_k=10):
            return mock_citations

        artifact = generate_issue_table(
            db, str(test_matter.id), attorney_user,
            query_text="legal issues", top_k=5,
            retriever=fake_retrieve,
        )
        assert artifact.artifact_type == "issue_table"
        assert artifact.status == "draft"
        assert "issues" in artifact.content

    def test_generate_memo_requires_question(self, db, attorney_user, test_matter):
        """Memo generation requires a question."""
        def fake_retrieve(db, matter_id, query, top_k=10):
            return [_make_mock_citation()]

        with pytest.raises(ArtifactError):
            generate_memo(
                db, str(test_matter.id), attorney_user,
                question="", retriever=fake_retrieve,
            )

    def test_artifact_workflow_state_transitions(self, db, attorney_user, test_matter):
        """Artifact moves through draft -> under_review -> approved."""
        mock_citations = [_make_mock_citation()]

        def fake_retrieve(db, matter_id, query, top_k=10):
            return mock_citations

        artifact = generate_memo(
            db, str(test_matter.id), attorney_user,
            question="What is the liability?",
            retriever=fake_retrieve,
        )
        assert artifact.status == "draft"

        artifact = submit_for_review(db, str(artifact.id), attorney_user)
        assert artifact.status == "under_review"

        artifact = approve_artifact(db, str(artifact.id), attorney_user)
        assert artifact.status == "approved"
        assert artifact.approved_by == attorney_user.id

    def test_reject_artifact_requires_reason(self, db, attorney_user, test_matter):
        """Rejection requires a reason."""
        mock_citations = [_make_mock_citation()]

        def fake_retrieve(db, matter_id, query, top_k=10):
            return mock_citations

        artifact = generate_memo(
            db, str(test_matter.id), attorney_user,
            question="What is the liability?",
            retriever=fake_retrieve,
        )
        with pytest.raises(ArtifactError):
            reject_artifact(db, str(artifact.id), attorney_user, reason="")

    def test_list_artifacts_by_type(self, db, attorney_user, test_matter):
        """Filter artifacts by type."""
        mock_citations = [_make_mock_citation()]

        def fake_retrieve(db, matter_id, query, top_k=10):
            return mock_citations

        generate_chronology(
            db, str(test_matter.id), attorney_user,
            query_text="events", retriever=fake_retrieve,
        )
        generate_chronology(
            db, str(test_matter.id), attorney_user,
            query_text="timeline", retriever=fake_retrieve,
        )
        generate_memo(
            db, str(test_matter.id), attorney_user,
            question="Question?", retriever=fake_retrieve,
        )

        all_artifacts = list_artifacts(db, str(test_matter.id), attorney_user)
        assert len(all_artifacts) >= 3

        chronologies = list_artifacts(db, str(test_matter.id), attorney_user, "chronology")
        assert len(chronologies) >= 2

        memos = list_artifacts(db, str(test_matter.id), attorney_user, "memo")
        assert len(memos) >= 1

    def test_version_snapshots(self, db, attorney_user, test_matter):
        """Updates create version snapshots."""
        mock_citations = [_make_mock_citation()]

        def fake_retrieve(db, matter_id, query, top_k=10):
            return mock_citations

        artifact = generate_memo(
            db, str(test_matter.id), attorney_user,
            question="What is the liability?",
            retriever=fake_retrieve,
        )
        versions_before = get_artifact_versions(db, str(artifact.id), attorney_user)

        update_artifact_content(
            db, str(artifact.id), attorney_user,
            content={"analysis": {"draft": "Updated analysis"}},
        )

        versions_after = get_artifact_versions(db, str(artifact.id), attorney_user)
        assert len(versions_after) == len(versions_before) + 1

    def test_approval_ledger_records_all_actions(self, db, attorney_user, test_matter):
        """Every state change is recorded in approval ledger."""
        mock_citations = [_make_mock_citation()]

        def fake_retrieve(db, matter_id, query, top_k=10):
            return mock_citations

        artifact = generate_memo(
            db, str(test_matter.id), attorney_user,
            question="What is the liability?",
            retriever=fake_retrieve,
        )
        submit_for_review(db, str(artifact.id), attorney_user)
        approve_artifact(db, str(artifact.id), attorney_user)

        history = get_approval_history(db, str(artifact.id), attorney_user)
        assert len(history) >= 2

    def test_get_artifact_not_found(self, db, attorney_user):
        """Getting a nonexistent artifact raises ArtifactError."""
        with pytest.raises(ArtifactError):
            get_artifact(db, str(uuid.uuid4()), attorney_user)

    def test_update_approved_artifact_fails(self, db, attorney_user, test_matter):
        """Cannot update an approved artifact."""
        mock_citations = [_make_mock_citation()]

        def fake_retrieve(db, matter_id, query, top_k=10):
            return mock_citations

        artifact = generate_memo(
            db, str(test_matter.id), attorney_user,
            question="What is the liability?",
            retriever=fake_retrieve,
        )
        submit_for_review(db, str(artifact.id), attorney_user)
        approve_artifact(db, str(artifact.id), attorney_user)

        with pytest.raises(ArtifactError):
            update_artifact_content(
                db, str(artifact.id), attorney_user, {"test": "data"}
            )


class TestArtifactAPI:
    """Test artifact HTTP endpoints (via FastAPI test client)."""

    def test_unauthenticated_returns_401(self):
        """Endpoints require authentication."""
        from fastapi.testclient import TestClient
        from app.main import create_app

        app = create_app()
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/matters/00000000-0000-0000-0000-000000000001/artifacts",
                json={"artifact_type": "memo", "query_text": "test"},
            )
            assert resp.status_code == 401
