# Ganymede API — Adversarial Fixture Test
"""Test adversarial fixtures: corrupt, duplicate, rotated, tables."""

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import get_settings
from app.models import Base, Tenant, Matter, Document, Page
from app.services.ingestion import ingest_document

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "testdata", "fixtures")
CORPUS_A = os.path.join(os.path.dirname(__file__), "..", "..", "testdata", "corpus-v0.1")

MIME_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def get_mime_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return MIME_MAP.get(ext, "application/octet-stream")


def _ingest_fixture(db, matter_id, filename, expect_status):
    filepath = os.path.join(FIXTURES_DIR, filename)
    if not os.path.exists(filepath):
        return {"skipped": True, "filename": filename}

    mime_type = get_mime_type(filename)
    with open(filepath, "rb") as f:
        file_bytes = f.read()

    doc = ingest_document(
        db=db,
        matter_id=matter_id,
        filename=filename,
        file_bytes=file_bytes,
        mime_type=mime_type,
    )

    page_count = db.query(Page).filter(Page.document_id == doc.id).count()
    status_ok = doc.ingestion_status == expect_status

    return {
        "skipped": False,
        "filename": filename,
        "status": doc.ingestion_status,
        "expected": expect_status,
        "status_ok": status_ok,
        "page_count": page_count,
        "is_duplicate": doc.is_duplicate,
    }


def test_adversarial_fixtures():
    db = SessionLocal()
    try:
        # Get or create test matter
        matter = db.query(Matter).filter(Matter.name.like("%Test%")).first()
        if not matter:
            tenant = db.query(Tenant).first()
            matter = Matter(
                id="00000000-0000-0000-0000-000000000099",
                tenant_id=tenant.id,
                name="Test Matter - Adversarial",
            )
            db.add(matter)
            db.commit()

        # Test 1: Corrupt PDF - should fail visibly
        r1 = _ingest_fixture(db, str(matter.id), "adversarial-corrupt.pdf", "failed")
        if not r1["skipped"]:
            assert r1["status_ok"], f"Corrupt PDF: expected failed, got {r1['status']}"

        # Test 2: Rotated pages - should parse (possibly partial)
        r2 = _ingest_fixture(db, str(matter.id), "adversarial-rotated.pdf", "completed")
        if not r2["skipped"]:
            assert r2["status_ok"], f"Rotated PDF: expected completed, got {r2['status']}"

        # Test 3: DOCX with tables - should parse
        r3 = _ingest_fixture(db, str(matter.id), "adversarial-tables.docx", "completed")
        if not r3["skipped"]:
            assert r3["status_ok"], f"Tables DOCX: expected completed, got {r3['status']}"

        # Test 4: Duplicate - should be detected
        orig_path = os.path.join(CORPUS_A, "DOC-001-Complaint.pdf")
        if os.path.exists(orig_path):
            with open(orig_path, "rb") as f:
                orig_bytes = f.read()
            orig_doc = ingest_document(
                db=db,
                matter_id=str(matter.id),
                filename="DOC-001-Complaint.pdf",
                file_bytes=orig_bytes,
                mime_type="application/pdf",
            )
            r4 = _ingest_fixture(db, str(matter.id), "adversarial-duplicate.pdf", "completed")
            if not r4["skipped"]:
                assert r4["is_duplicate"], "Duplicate PDF should be detected as duplicate"

    finally:
        db.close()
