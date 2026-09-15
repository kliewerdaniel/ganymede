# Ganymede API — Artifact Services

"""Structured artifact generation: chronology, issue table, memo.

Each artifact is generated from retrieved citations and stored with full
provenance. Artifacts go through a review workflow: draft → under_review →
approved/rejected. All status changes are recorded in the approval ledger.

Architecture: retrieval is separated from artifact building so both can be
tested independently. The generate_* functions retrieve citations and pass
them to build_* helpers that construct the content dict.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from sqlalchemy.orm import Session

from app.models import (
    Artifact, ArtifactVersion, Approval,
    Matter, User, Chunk, Page, Document,
)
from app.services.retrieval import retrieve as default_retrieve
from app.services.query_expansion import expand_query

logger = logging.getLogger(__name__)


class ArtifactError(Exception):
    """Artifact operation error."""
    def __init__(self, message: str):
        self.message = message


# --- Access Control ---


def _require_matter_access(db: Session, user: User, matter_id: str):
    """Verify user has access to the matter."""
    from app.core.rbac import can_access_matter
    can_access_matter(user, matter_id, db)


# --- Version Management ---


def _create_version(db: Session, artifact: Artifact, user_id: str,
                    change_description: Optional[str] = None) -> ArtifactVersion:
    """Create a new version snapshot for an artifact."""
    max_ver = max((v.version for v in artifact.versions), default=0)
    version = ArtifactVersion(
        artifact_id=artifact.id,
        version=max_ver + 1,
        content=artifact.content,
        change_description=change_description,
        created_by=user_id,
    )
    db.add(version)
    db.flush()
    return version


# --- Approval Ledger ---


def _record_approval(db: Session, artifact_id: str, action: str,
                     user: User, prior_status: Optional[str], new_status: str,
                     comment: Optional[str] = None) -> Approval:
    """Record an approval action in the ledger."""
    approval = Approval(
        artifact_id=artifact_id,
        action=action,
        performed_by=user.id,
        prior_status=prior_status,
        new_status=new_status,
        comment=comment,
    )
    db.add(approval)
    db.flush()
    return approval


# --- Citation-to-Source Helper ---


def _citation_to_source(db: Session, c) -> Dict[str, Any]:
    """Convert a citation object to a source reference dict."""
    doc = db.query(Document).filter(Document.id == c.document_id).first()
    return {
        "document_id": str(c.document_id),
        "document_name": doc.original_filename if doc else "Unknown",
        "page": c.page,
        "start_offset": c.start_offset,
        "end_offset": c.end_offset,
        "sha256": c.sha256,
    }


# --- Artifact Builders ---


def _build_chronology_from_citations(
    db: Session,
    citations: List,
    query_text: str = None,
) -> Dict[str, Any]:
    """Build chronology content from a list of citations."""
    events = []
    for i, c in enumerate(citations):
        events.append({
            "index": i,
            "date": None,
            "date_confidence": "unextracted",
            "event": c.quoted_text[:500] if c.quoted_text else "",
            "actor": None,
            "source": _citation_to_source(db, c),
            "citation_index": i,
        })

    return {
        "events": events,
        "unextracted_count": len(events),
        "date_range": {"earliest": None, "latest": None},
        "generated_from_query": query_text,
        "citation_count": len(citations),
    }


def _build_issue_table_from_citations(
    db: Session,
    citations: List,
    query_text: str = None,
) -> Dict[str, Any]:
    """Build issue table content from a list of citations."""
    issues = []
    for i, c in enumerate(citations):
        issues.append({
            "index": i,
            "issue": c.quoted_text[:300] if c.quoted_text else "",
            "status": "unreviewed",
            "support": [_citation_to_source(db, c)],
            "contrary": [],
            "gap": [],
            "notes": None,
        })

    return {
        "issues": issues,
        "unreviewed_count": len(issues),
        "generated_from_query": query_text,
        "citation_count": len(citations),
    }


def _build_memo_from_citations(
    db: Session,
    citations: List,
    question: str,
) -> Dict[str, Any]:
    """Build memo content from a list of citations."""
    record_passages = [_citation_to_source(db, c) for c in citations]

    return {
        "question": question,
        "record": {
            "passages": record_passages,
            "citation_count": len(record_passages),
        },
        "analysis": {
            "draft": None,
            "constraints": "Analysis must be supported by record passages only.",
        },
        "limits": {
            "scope": "Constrained to uploaded matter documents only",
            "disclaimer": "AI-assisted draft — attorney review required",
            "generated_at": datetime.utcnow().isoformat(),
        },
        "generated_from_query": question,
        "citation_count": len(citations),
    }


# --- Artifact Persistence ---


def _persist_artifact(
    db: Session,
    matter_id: str,
    artifact_type: str,
    title: str,
    content: Dict[str, Any],
    user: User,
    query_text: Optional[str] = None,
    citations: Optional[List] = None,
) -> Artifact:
    """Create and persist an artifact with version + approval."""
    artifact = Artifact(
        id=uuid.uuid4(),
        matter_id=matter_id,
        artifact_type=artifact_type,
        title=title,
        status="draft",
        source_query=query_text,
        source_citation_ids=[str(c.document_id) for c in (citations or [])],
        content=content,
        created_by=user.id,
    )
    db.add(artifact)
    db.flush()

    _create_version(db, artifact, str(user.id), "Initial generation")
    _record_approval(db, str(artifact.id), "create", user, None, "draft")

    db.commit()
    return artifact


# --- Public API: Generate Artifacts ---


def generate_chronology(
    db: Session,
    matter_id: str,
    user: User,
    query_text: Optional[str] = None,
    top_k: int = 20,
    retriever: Optional[Callable] = None,
) -> Artifact:
    """Generate a chronology artifact from matter documents."""
    _require_matter_access(db, user, matter_id)

    if retriever is None:
        retriever = default_retrieve

    search_query = query_text or "timeline events dates chronology"
    expanded = expand_query(search_query)
    citations = retriever(db, matter_id, expanded, top_k=top_k)

    if not citations:
        raise ArtifactError("No relevant passages found for chronology")

    content = _build_chronology_from_citations(db, citations, query_text)

    return _persist_artifact(
        db, matter_id, "chronology",
        f"Chronology: {query_text or 'Full Matter'}",
        content, user, query_text, citations,
    )


def generate_issue_table(
    db: Session,
    matter_id: str,
    user: User,
    query_text: Optional[str] = None,
    top_k: int = 20,
    retriever: Optional[Callable] = None,
) -> Artifact:
    """Generate an issue table artifact from matter documents."""
    _require_matter_access(db, user, matter_id)

    if retriever is None:
        retriever = default_retrieve

    search_query = query_text or "legal issues claims defenses evidence"
    expanded = expand_query(search_query)
    citations = retriever(db, matter_id, expanded, top_k=top_k)

    if not citations:
        raise ArtifactError("No relevant passages found for issue table")

    content = _build_issue_table_from_citations(db, citations, query_text)

    return _persist_artifact(
        db, matter_id, "issue_table",
        f"Issue Table: {query_text or 'Full Matter'}",
        content, user, query_text, citations,
    )


def generate_memo(
    db: Session,
    matter_id: str,
    user: User,
    question: str,
    top_k: int = 10,
    retriever: Optional[Callable] = None,
) -> Artifact:
    """Generate an internal memo artifact."""
    _require_matter_access(db, user, matter_id)

    if not question:
        raise ArtifactError("Memo requires a question")

    if retriever is None:
        retriever = default_retrieve

    expanded = expand_query(question)
    citations = retriever(db, matter_id, expanded, top_k=top_k)

    if not citations:
        raise ArtifactError("No relevant passages found for memo")

    content = _build_memo_from_citations(db, citations, question)

    return _persist_artifact(
        db, matter_id, "memo",
        f"Memo: {question[:100]}",
        content, user, question, citations,
    )


# --- Public API: Read Artifacts ---


def get_artifact(db: Session, artifact_id: str, user: User) -> Artifact:
    """Get an artifact by ID with access check."""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise ArtifactError("Artifact not found")
    _require_matter_access(db, user, str(artifact.matter_id))
    return artifact


def list_artifacts(db: Session, matter_id: str, user: User,
                   artifact_type: str = None) -> List[Artifact]:
    """List artifacts for a matter, optionally filtered by type."""
    _require_matter_access(db, user, matter_id)
    query = db.query(Artifact).filter(Artifact.matter_id == matter_id)
    if artifact_type:
        query = query.filter(Artifact.artifact_type == artifact_type)
    return query.order_by(Artifact.created_at.desc()).all()


# --- Public API: Update Artifacts ---


def update_artifact_content(db: Session, artifact_id: str, user: User,
                            content: Dict[str, Any],
                            change_description: str = None) -> Artifact:
    """Update artifact content, creating a new version."""
    artifact = get_artifact(db, artifact_id, user)

    if artifact.status in ("approved", "rejected"):
        raise ArtifactError(f"Cannot update {artifact.status} artifact")

    _create_version(db, artifact, str(user.id), change_description)

    artifact.content.update(content)
    artifact.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(artifact)
    return artifact


# --- Public API: Review Workflow ---


def submit_for_review(db: Session, artifact_id: str, user: User) -> Artifact:
    """Submit a draft artifact for review."""
    artifact = get_artifact(db, artifact_id, user)

    if artifact.status != "draft":
        raise ArtifactError(f"Only drafts can be submitted, current status: {artifact.status}")

    prior = artifact.status
    artifact.status = "under_review"
    _record_approval(db, artifact_id, "submit_for_review", user, prior, "under_review")

    db.commit()
    db.refresh(artifact)
    return artifact


def approve_artifact(db: Session, artifact_id: str, user: User,
                     comment: Optional[str] = None) -> Artifact:
    """Approve an artifact. Only matter leads and admins."""
    artifact = get_artifact(db, artifact_id, user)

    from app.services.membership import is_matter_lead
    if user.role != "administrator" and not is_matter_lead(db, str(user.id), str(artifact.matter_id)):
        raise ArtifactError("Only matter leads or admins can approve")

    if artifact.status not in ("draft", "under_review"):
        raise ArtifactError(f"Cannot approve artifact with status: {artifact.status}")

    prior = artifact.status
    artifact.status = "approved"
    artifact.approved_by = user.id
    artifact.approved_at = datetime.utcnow()
    _record_approval(db, artifact_id, "approve", user, prior, "approved", comment)

    db.commit()
    db.refresh(artifact)
    return artifact


def reject_artifact(db: Session, artifact_id: str, user: User,
                    reason: str) -> Artifact:
    """Reject an artifact with a reason."""
    artifact = get_artifact(db, artifact_id, user)

    from app.services.membership import is_matter_lead
    if user.role != "administrator" and not is_matter_lead(db, str(user.id), str(artifact.matter_id)):
        raise ArtifactError("Only matter leads or admins can reject")

    if artifact.status not in ("draft", "under_review"):
        raise ArtifactError(f"Cannot reject artifact with status: {artifact.status}")

    if not reason:
        raise ArtifactError("Rejection requires a reason")

    prior = artifact.status
    artifact.status = "rejected"
    artifact.rejection_reason = reason
    artifact.rejection_by = user.id
    artifact.rejection_at = datetime.utcnow()
    _record_approval(db, artifact_id, "reject", user, prior, "rejected", reason)

    db.commit()
    db.refresh(artifact)
    return artifact


# --- Public API: History ---


def get_artifact_versions(db: Session, artifact_id: str, user: User) -> List[ArtifactVersion]:
    """Get version history for an artifact."""
    get_artifact(db, artifact_id, user)
    return db.query(ArtifactVersion).filter(
        ArtifactVersion.artifact_id == artifact_id
    ).order_by(ArtifactVersion.version.desc()).all()


def get_approval_history(db: Session, artifact_id: str, user: User) -> List[Approval]:
    """Get approval ledger entries for an artifact."""
    get_artifact(db, artifact_id, user)
    return db.query(Approval).filter(
        Approval.artifact_id == artifact_id
    ).order_by(Approval.performed_at.desc()).all()
