# Ganymede API — Async Verification Service

"""Asynchronous verification with background processing.

Week 5 approach: return raw results immediately, verify in background,
update via polling or WebSocket. This gives users < 1s initial response
with full verification happening asynchronously.

Design:
1. POST /ask → returns immediately with raw citations + query_id
2. Verification runs in background thread
3. GET /ask/{query_id}/status → returns verification progress
4. When complete, verified citations replace raw ones in the response
"""

import threading
import time
import uuid
from typing import Dict, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

# Background executor for verification tasks
_executor = ThreadPoolExecutor(max_workers=2)

# In-memory store for query results (in production, use Redis or DB)
_query_store: Dict[str, "QueryStatus"] = {}
_store_lock = threading.Lock()


@dataclass
class QueryStatus:
    """Track the status of an async query."""
    query_id: str
    matter_id: str
    question: str
    expanded_query: str
    created_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending → retrieving → verifying → complete
    raw_citations: list = field(default_factory=list)
    verified_citations: list = field(default_factory=list)
    error: Optional[str] = None
    raw_count: int = 0
    verified_count: int = 0
    retrieval_time_ms: float = 0
    verification_time_ms: float = 0


def submit_query(
    matter_id: str,
    question: str,
    db_session_factory,
    top_k: int = 5,
) -> str:
    """Submit a query for async processing.

    Returns immediately with a query_id. The query is processed in background:
    1. Retrieval (with query expansion)
    2. Verification (LLM-based)

    Args:
        matter_id: matter to search
        question: user's question
        db_session_factory: callable that returns a DB session
        top_k: number of raw citations to retrieve

    Returns:
        query_id for polling status
    """
    query_id = str(uuid.uuid4())

    status = QueryStatus(
        query_id=query_id,
        matter_id=matter_id,
        question=question,
        expanded_query="",
    )

    with _store_lock:
        _query_store[query_id] = status

    # Submit to background executor
    _executor.submit(_process_query, query_id, db_session_factory, top_k)

    return query_id


def _process_query(query_id: str, db_session_factory, top_k: int):
    """Background task: retrieve + verify."""
    from app.services.retrieval import retrieve
    from app.services.query_expansion import expand_query
    from app.services.verifier import verify_top_k

    status = _query_store.get(query_id)
    if not status:
        return

    try:
        # Retrieval phase
        status.status = "retrieving"
        t0 = time.time()

        db = db_session_factory()
        try:
            status.expanded_query = expand_query(status.question)
            raw_citations = retrieve(
                db, status.matter_id, status.expanded_query, top_k=top_k
            )
            status.raw_citations = [
                {
                    "document_id": str(c.document_id),
                    "sha256": c.sha256,
                    "page": c.page,
                    "start_offset": c.start_offset,
                    "end_offset": c.end_offset,
                    "quoted_text": c.quoted_text,
                    "parser_version": c.parser_version,
                    "retrieval_scores": c.retrieval_scores,
                    "access_scope": c.access_scope,
                    "model_version": c.model_version,
                }
                for c in raw_citations
            ]
            status.raw_count = len(raw_citations)
        finally:
            db.close()

        status.retrieval_time_ms = (time.time() - t0) * 1000

        # Verification phase
        if status.raw_count > 0:
            status.status = "verifying"
            t1 = time.time()

            db = db_session_factory()
            try:
                # Re-create Citation objects for verification
                from app.services.retrieval import Citation
                citations = []
                for c in status.raw_citations:
                    cite = Citation(
                        matter_id=status.matter_id,
                        document_id=c["document_id"],
                        sha256=c["sha256"],
                        page=c["page"],
                        start_offset=c["start_offset"],
                        end_offset=c["end_offset"],
                        quoted_text=c["quoted_text"],
                        parser_version=c["parser_version"],
                        retrieval_scores=c["retrieval_scores"],
                        access_scope=c["access_scope"],
                        model_version=c["model_version"],
                    )
                    citations.append(cite)

                verified = verify_top_k(
                    status.question, citations, top_k_verify=len(citations)
                )
                status.verified_citations = [
                    {
                        "document_id": str(c.document_id),
                        "sha256": c.sha256,
                        "page": c.page,
                        "start_offset": c.start_offset,
                        "end_offset": c.end_offset,
                        "quoted_text": c.quoted_text,
                        "parser_version": c.parser_version,
                        "retrieval_scores": c.retrieval_scores,
                        "access_scope": c.access_scope,
                        "model_version": c.model_version,
                    }
                    for c in verified
                ]
                status.verified_count = len(verified)
            finally:
                db.close()

            status.verification_time_ms = (time.time() - t1) * 1000

        status.status = "complete"

    except Exception as e:
        status.status = "error"
        status.error = str(e)


def get_query_status(query_id: str) -> Optional[dict]:
    """Get the current status of an async query.

    Returns:
        dict with status, citations, timing info, or None if not found
    """
    status = _query_store.get(query_id)
    if not status:
        return None

    # If still processing, return raw citations for immediate display
    if status.status in ("pending", "retrieving"):
        return {
            "query_id": query_id,
            "status": status.status,
            "question": status.question,
            "expanded_query": status.expanded_query,
            "citations": status.raw_citations,
            "result_count": status.raw_count,
            "verification_pending": True,
            "retrieval_time_ms": status.retrieval_time_ms,
        }

    # If verifying, return raw with pending flag
    if status.status == "verifying":
        return {
            "query_id": query_id,
            "status": status.status,
            "question": status.question,
            "expanded_query": status.expanded_query,
            "citations": status.raw_citations,
            "result_count": status.raw_count,
            "verification_pending": True,
            "retrieval_time_ms": status.retrieval_time_ms,
            "verification_time_ms": status.verification_time_ms,
        }

    # If complete, return verified citations
    if status.status == "complete":
        return {
            "query_id": query_id,
            "status": status.status,
            "question": status.question,
            "expanded_query": status.expanded_query,
            "citations": status.verified_citations,
            "result_count": status.verified_count,
            "verification_pending": False,
            "raw_count": status.raw_count,
            "retrieval_time_ms": status.retrieval_time_ms,
            "verification_time_ms": status.verification_time_ms,
        }

    # Error
    return {
        "query_id": query_id,
        "status": status.status,
        "question": status.question,
        "error": status.error,
    }


def cleanup_old_queries(max_age_s: float = 3600):
    """Remove queries older than max_age_s from the store."""
    cutoff = time.time() - max_age_s
    with _store_lock:
        to_remove = [
            k for k, v in _query_store.items()
            if v.created_at < cutoff
        ]
        for k in to_remove:
            del _query_store[k]
