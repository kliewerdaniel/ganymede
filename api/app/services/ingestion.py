# Ganymede API — Ingestion Service

"""Orchestrates document ingestion with provenance and failure visibility."""

import os
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Document, Page, IngestionJob
from app.services.parser import route_and_parse, compute_sha256
from app.core.config import get_settings

settings = get_settings()


class IngestionError(Exception):
    """Raised when ingestion fails."""
    pass


def check_duplicate(db: Session, matter_id: str, sha256: str) -> Optional[Document]:
    """Check if a document with the same hash already exists in the matter."""
    return db.query(Document).filter(
        Document.matter_id == matter_id,
        Document.sha256 == sha256,
    ).first()


def create_ingestion_job(db: Session, document_id: str) -> IngestionJob:
    """Create a new ingestion job for a document."""
    job = IngestionJob(
        document_id=document_id,
        status="pending",
        stage="upload",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job_status(
    db: Session,
    job: IngestionJob,
    status: str,
    stage: Optional[str] = None,
    error_message: Optional[str] = None,
):
    """Update ingestion job status."""
    job.status = status
    if stage:
        job.stage = stage
    if error_message:
        job.error_message = error_message
    if status == "processing" and not job.started_at:
        job.started_at = datetime.utcnow()
    if status in ("completed", "failed"):
        job.completed_at = datetime.utcnow()
    db.commit()


def ingest_document(
    db: Session,
    matter_id: str,
    filename: str,
    file_bytes: bytes,
    mime_type: str,
) -> Document:
    """
    Ingest a document: parse, extract pages, record provenance.

    Returns the created Document. On failure, the document is marked as failed
    with a visible error — never silently empty.
    """
    # Validate MIME type
    if mime_type not in settings.ALLOWED_MIME_TYPES:
        raise IngestionError(f"Unsupported MIME type: {mime_type}")

    # Validate file size
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
        raise IngestionError(
            f"File size {len(file_bytes)} exceeds maximum {settings.MAX_UPLOAD_SIZE}"
        )

    # Compute content hash
    sha256 = compute_sha256(file_bytes)

    # Check for duplicate
    existing = check_duplicate(db, matter_id, sha256)
    is_duplicate = existing is not None

    # Create document record
    doc = Document(
        id=uuid.uuid4(),
        matter_id=matter_id,
        filename=f"{uuid.uuid4()}_{filename}",  # UUID prefix to prevent collisions
        original_filename=filename,
        mime_type=mime_type,
        size_bytes=len(file_bytes),
        sha256=sha256,
        is_duplicate=is_duplicate,
        duplicate_of_id=existing.id if existing else None,
        ingestion_status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Create ingestion job
    job = create_ingestion_job(db, str(doc.id))

    try:
        # Parse the document
        update_job_status(db, job, "processing", "parse")
        result = route_and_parse(file_bytes, mime_type)

        # Update document with parse results
        doc.page_count = result.page_count
        doc.parser_version = result.parser_version

        # Create page records with provenance
        for page_result in result.pages:
            page = Page(
                id=uuid.uuid4(),
                document_id=doc.id,
                page_number=page_result.page_number,
                text=page_result.text,
                start_offset=page_result.start_offset,
                end_offset=page_result.end_offset,
                parser_version=page_result.parser_version,
            )
            db.add(page)

        # Mark as completed
        doc.ingestion_status = "completed"
        update_job_status(db, job, "completed")
        db.commit()

    except Exception as e:
        # Mark as failed with visible error
        doc.ingestion_status = "failed"
        doc.ingestion_error = str(e)
        update_job_status(db, job, "failed", error_message=str(e))
        db.commit()

    return doc


def get_ingestion_status(db: Session, document_id: str) -> Optional[Document]:
    """Get the ingestion status of a document."""
    return db.query(Document).filter(Document.id == document_id).first()
