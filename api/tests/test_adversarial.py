# Ganymede API — Adversarial Fixture Test

"""Test adversarial fixtures: corrupt, duplicate, rotated, tables."""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models import Base, Tenant, Matter, Document, Page
from app.services.ingestion import ingest_document

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

FIXTURES_DIR = "/Users/danielkliewer/Projects/ganymede/testdata/fixtures"
CORPUS_A = "/Users/danielkliewer/Projects/ganymede/testdata/corpus-v0.1"

MIME_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def get_mime_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return MIME_MAP.get(ext, "application/octet-stream")


def test_fixture(db, matter_id: str, filename: str, expect_status: str, description: str):
    """Test a single fixture."""
    filepath = os.path.join(FIXTURES_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  SKIP: {filename} not found")
        return

    mime_type = get_mime_type(filename)
    file_size = os.path.getsize(filepath)

    print(f"\n[{filename}]")
    print(f"  Description: {description}")
    print(f"  MIME: {mime_type}, Size: {file_size} bytes")

    with open(filepath, "rb") as f:
        file_bytes = f.read()

    try:
        doc = ingest_document(
            db=db,
            matter_id=matter_id,
            filename=filename,
            file_bytes=file_bytes,
            mime_type=mime_type,
        )

        page_count = db.query(Page).filter(Page.document_id == doc.id).count()

        status_match = "✓" if doc.ingestion_status == expect_status else "✗ UNEXPECTED"
        print(f"  {status_match} Status: {doc.ingestion_status} (expected: {expect_status})")
        print(f"    Pages: {page_count}")
        if doc.is_duplicate:
            print(f"    ⚠ DUPLICATE detected (duplicate_of: {doc.duplicate_of_id})")
        if doc.ingestion_error:
            print(f"    Error: {doc.ingestion_error}")

    except Exception as e:
        if expect_status == "failed":
            print(f"  ✓ Expected failure: {str(e)}")
        else:
            print(f"  ✗ Unexpected error: {str(e)}")


def main():
    db = SessionLocal()
    try:
        # Get or create matter
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

        print("=" * 60)
        print("Adversarial Fixture Tests")
        print("=" * 60)

        # Test 1: Corrupt PDF - should fail visibly (0 pages)
        test_fixture(
            db, str(matter.id), "adversarial-corrupt.pdf", "failed",
            "Corrupt PDF with invalid structure (should produce 0 pages and fail)"
        )

        # Test 2: Rotated pages - should parse (possibly partial)
        test_fixture(
            db, str(matter.id), "adversarial-rotated.pdf", "completed",
            "PDF with rotated pages (90°, 180°)"
        )

        # Test 3: DOCX with tables - should parse
        test_fixture(
            db, str(matter.id), "adversarial-tables.docx", "completed",
            "DOCX with tables"
        )

        # Test 4: Duplicate - should be detected
        # First, ingest the original from corpus A
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
            print(f"\n[Original DOC-001 ingested] SHA256: {orig_doc.sha256[:16]}...")

        # Now test the duplicate
        test_fixture(
            db, str(matter.id), "adversarial-duplicate.pdf", "completed",
            "Duplicate of DOC-001 (should be detected)"
        )

        print("\n" + "=" * 60)
        print("Adversarial tests complete")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
