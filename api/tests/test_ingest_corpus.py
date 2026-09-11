# Ganymede — Frozen Corpus Ingestion Test

"""Ingest the frozen corpus and report per-file results."""

import os
import sys
import time
from pathlib import Path

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models import Base, Tenant, Matter, Document, Page
from app.services.ingestion import ingest_document

# Initialize database
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Corpus paths
CORPUS_A = "/Users/danielkliewer/Projects/ganymede/testdata/corpus-v0.1"
CORPUS_B = "/Users/danielkliewer/Projects/ganymede/testdata/corpus-v0.1-matter-b"

# MIME type mapping
MIME_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".txt": "text/plain",
}


def get_mime_type(filename: str) -> str:
    """Get MIME type from file extension."""
    ext = Path(filename).suffix.lower()
    return MIME_MAP.get(ext, "application/octet-stream")


def ingest_corpus(db, matter_id: str, corpus_path: str, corpus_name: str):
    """Ingest all files in a corpus directory."""
    results = []
    files = sorted([
        f for f in os.listdir(corpus_path)
        if not f.startswith(".") and not f.endswith(".md") and not f.endswith(".py")
    ])

    print(f"\n{'='*60}")
    print(f"Ingesting {corpus_name}: {len(files)} files")
    print(f"{'='*60}")

    for filename in files:
        filepath = os.path.join(corpus_path, filename)
        if not os.path.isfile(filepath):
            continue

        mime_type = get_mime_type(filename)
        file_size = os.path.getsize(filepath)

        print(f"\n[{filename}] ({mime_type}, {file_size} bytes)")

        try:
            with open(filepath, "rb") as f:
                file_bytes = f.read()

            start_time = time.time()
            doc = ingest_document(
                db=db,
                matter_id=matter_id,
                filename=filename,
                file_bytes=file_bytes,
                mime_type=mime_type,
            )
            elapsed = time.time() - start_time

            # Count pages
            page_count = db.query(Page).filter(Page.document_id == doc.id).count()

            status_icon = "✓" if doc.ingestion_status == "completed" else "✗"
            print(f"  {status_icon} Status: {doc.ingestion_status}")
            print(f"    SHA256: {doc.sha256[:16]}...")
            print(f"    Pages: {page_count}")
            print(f"    Parser: {doc.parser_version}")
            print(f"    Time: {elapsed:.2f}s")
            if doc.is_duplicate:
                print(f"    ⚠ DUPLICATE of {doc.duplicate_of_id}")
            if doc.ingestion_error:
                print(f"    Error: {doc.ingestion_error}")

            results.append({
                "filename": filename,
                "status": doc.ingestion_status,
                "pages": page_count,
                "parser": doc.parser_version,
                "time": elapsed,
                "is_duplicate": doc.is_duplicate,
                "error": doc.ingestion_error,
            })

        except Exception as e:
            print(f"  ✗ FAILED: {str(e)}")
            results.append({
                "filename": filename,
                "status": "failed",
                "pages": 0,
                "parser": None,
                "time": 0,
                "is_duplicate": False,
                "error": str(e),
            })

    return results


def print_summary(results: list, corpus_name: str):
    """Print summary statistics."""
    total = len(results)
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = sum(1 for r in results if r["status"] == "failed")
    duplicates = sum(1 for r in results if r["is_duplicate"])

    print(f"\n{'='*60}")
    print(f"Summary: {corpus_name}")
    print(f"{'='*60}")
    print(f"Total files: {total}")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Duplicates: {duplicates}")
    print(f"Success rate: {completed/total*100:.1f}%")

    if failed > 0:
        print(f"\nFailed files:")
        for r in results:
            if r["status"] == "failed":
                print(f"  - {r['filename']}: {r['error']}")


def main():
    db = SessionLocal()
    try:
        # Create default tenant
        tenant = db.query(Tenant).first()
        if not tenant:
            tenant = Tenant(
                id="00000000-0000-0000-0000-000000000001",
                name="Default Tenant",
            )
            db.add(tenant)
            db.commit()

        # Create matters for each corpus (idempotent)
        matter_a = db.query(Matter).filter(Matter.id == "00000000-0000-0000-0000-000000000011").first()
        if not matter_a:
            matter_a = Matter(
                id="00000000-0000-0000-0000-000000000011",
                tenant_id=tenant.id,
                name="Matter A - Meridian v. Cascade",
                cause_number="D-2025-00418",
                court="Travis County District Court",
            )
            db.add(matter_a)
        matter_b = db.query(Matter).filter(Matter.id == "00000000-0000-0000-0000-000000000012").first()
        if not matter_b:
            matter_b = Matter(
                id="00000000-0000-0000-0000-000000000012",
                tenant_id=tenant.id,
                name="Matter B - Acme v. Whitfield",
                cause_number="D-2026-00187",
                court="Travis County District Court",
            )
            db.add(matter_b)
        db.commit()

        # Ingest corpora
        results_a = ingest_corpus(db, str(matter_a.id), CORPUS_A, "Matter A (Meridian v. Cascade)")
        results_b = ingest_corpus(db, str(matter_b.id), CORPUS_B, "Matter B (Acme v. Whitfield)")

        # Print summaries
        print_summary(results_a, "Matter A")
        print_summary(results_b, "Matter B")

        # Combined summary
        all_results = results_a + results_b
        total = len(all_results)
        completed = sum(1 for r in all_results if r["status"] == "completed")
        print(f"\n{'='*60}")
        print(f"COMBINED: {completed}/{total} files ingested successfully ({completed/total*100:.1f}%)")
        print(f"{'='*60}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
