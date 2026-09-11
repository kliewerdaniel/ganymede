# Ganymede — Provenance Audit

"""Audit provenance: verify spans resolve to correct document, page, and offsets."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models import Base, Tenant, Matter, Document, Page

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def audit_provenance(db, matter_id: str, sample_size: int = 5):
    """Audit provenance for a sample of pages in a matter."""
    pages = db.query(Page).join(Document).filter(
        Document.matter_id == matter_id
    ).order_by(Document.id, Page.page_number).limit(sample_size).all()

    print(f"\nProvenance audit: {len(pages)} sample pages")
    print("-" * 60)

    for page in pages:
        doc = page.document
        print(f"\nDocument: {doc.original_filename}")
        print(f"  Page {page.page_number}:")
        print(f"    Offsets: {page.start_offset} - {page.end_offset}")
        print(f"    Text length: {len(page.text)}")
        print(f"    Expected length: {page.end_offset - page.start_offset}")
        length_match = "✓" if len(page.text) == page.end_offset - page.start_offset else "✗ MISMATCH"
        print(f"    Length check: {length_match}")
        print(f"    Parser: {page.parser_version}")
        print(f"    SHA256: {doc.sha256[:16]}...")

        # Verify text is non-empty for non-duplicate docs
        if not doc.is_duplicate and not page.text.strip():
            print(f"    ⚠ WARNING: Page text is empty")


def main():
    db = SessionLocal()
    try:
        # Get matters
        matter_a = db.query(Matter).filter(Matter.name.like("%Matter A%")).first()
        matter_b = db.query(Matter).filter(Matter.name.like("%Matter B%")).first()

        if matter_a:
            print("\n" + "=" * 60)
            print("MATTER A (Meridian v. Cascade)")
            audit_provenance(db, str(matter_a.id), sample_size=5)

        if matter_b:
            print("\n" + "=" * 60)
            print("MATTER B (Acme v. Whitfield)")
            audit_provenance(db, str(matter_b.id), sample_size=5)

        # Summary statistics
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        total_docs = db.query(Document).count()
        total_pages = db.query(Page).count()
        completed_docs = db.query(Document).filter(Document.ingestion_status == "completed").count()
        failed_docs = db.query(Document).filter(Document.ingestion_status == "failed").count()
        duplicate_docs = db.query(Document).filter(Document.is_duplicate == True).count()

        print(f"Total documents: {total_docs}")
        print(f"Total pages: {total_pages}")
        print(f"Completed: {completed_docs}")
        print(f"Failed: {failed_docs}")
        print(f"Duplicates: {duplicate_docs}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
