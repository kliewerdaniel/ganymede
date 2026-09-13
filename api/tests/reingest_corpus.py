"""Re-ingest corpus-v0.1 and corpus-v0.1-matter-b into the database."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models import Tenant, Matter, Document
from app.services.ingestion import ingest_document
from app.services.chunker import chunk_all_pages
from app.services.embedding import embed_all_chunks

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def main():
    db = SessionLocal()
    try:
        # Create tenant
        tenant_id = "00000000-0000-0000-0000-000000000001"
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            tenant = Tenant(id=tenant_id, name="Default Tenant")
            db.add(tenant)
            db.commit()

        # Create matters
        matter_a = db.query(Matter).filter(Matter.name.like("%Matter A%")).first()
        if not matter_a:
            matter_a = Matter(
                id="00000000-0000-0000-0000-000000000011",
                tenant_id=tenant_id,
                name="Matter A - Meridian v. Cascade",
                description="Breach of contract dispute",
                cause_number="D-2025-001",
                court="Travis County District Court",
            )
            db.add(matter_a)
            db.commit()

        matter_b = db.query(Matter).filter(Matter.name.like("%Matter B%")).first()
        if not matter_b:
            matter_b = Matter(
                id="00000000-0000-0000-0000-000000000012",
                tenant_id=tenant_id,
                name="Matter B - Acme v. Whitfield",
                description="Employment dispute",
                cause_number="D-2025-002",
                court="Travis County District Court",
            )
            db.add(matter_b)
            db.commit()

        # Ingest corpus-v0.1
        corpus_dir = os.path.join(os.path.dirname(__file__), "..", "..", "testdata", "corpus-v0.1")
        print(f"Ingesting corpus-v0.1 from {corpus_dir}...")

        files = sorted([f for f in os.listdir(corpus_dir) if not f.startswith('.') and not f.endswith('.md') and not f.endswith('.py')])
        for filename in files:
            filepath = os.path.join(corpus_dir, filename)
            if not os.path.isfile(filepath):
                continue

            # Check if already existing
            existing = db.query(Document).filter(
                Document.original_filename == filename,
                Document.matter_id == str(matter_a.id),
            ).first()
            if existing:
                print(f"  SKIP (exists): {filename}")
                continue

            # Determine MIME type
            if filename.endswith('.pdf'):
                mime_type = "application/pdf"
            elif filename.endswith('.docx'):
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename.endswith('.txt'):
                mime_type = "text/plain"
            else:
                print(f"  SKIP (unknown type): {filename}")
                continue

            with open(filepath, 'rb') as f:
                file_bytes = f.read()

            try:
                doc = ingest_document(
                    db=db,
                    matter_id=str(matter_a.id),
                    filename=filename,
                    file_bytes=file_bytes,
                    mime_type=mime_type,
                )
                print(f"  OK: {filename} (pages={doc.page_count}, status={doc.ingestion_status})")
            except Exception as e:
                print(f"  FAIL: {filename} ({e})")

        # Ingest corpus-v0.1-matter-b
        corpus_b_dir = os.path.join(os.path.dirname(__file__), "..", "..", "testdata", "corpus-v0.1-matter-b")
        print(f"\nIngesting corpus-v0.1-matter-b from {corpus_b_dir}...")

        files_b = sorted([f for f in os.listdir(corpus_b_dir) if not f.startswith('.') and not f.endswith('.md') and not f.endswith('.py')])
        for filename in files_b:
            filepath = os.path.join(corpus_b_dir, filename)
            if not os.path.isfile(filepath):
                continue

            existing = db.query(Document).filter(
                Document.original_filename == filename,
                Document.matter_id == str(matter_b.id),
            ).first()
            if existing:
                print(f"  SKIP (exists): {filename}")
                continue

            if filename.endswith('.pdf'):
                mime_type = "application/pdf"
            elif filename.endswith('.docx'):
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename.endswith('.txt'):
                mime_type = "text/plain"
            else:
                print(f"  SKIP (unknown type): {filename}")
                continue

            with open(filepath, 'rb') as f:
                file_bytes = f.read()

            try:
                doc = ingest_document(
                    db=db,
                    matter_id=str(matter_b.id),
                    filename=filename,
                    file_bytes=file_bytes,
                    mime_type=mime_type,
                )
                print(f"  OK: {filename} (pages={doc.page_count}, status={doc.ingestion_status})")
            except Exception as e:
                print(f"  FAIL: {filename} ({e})")

        # Chunk and embed
        print("\nChunking pages...")
        total_chunks = chunk_all_pages(db)
        print(f"  Created {total_chunks} chunks")

        print("\nEmbedding chunks...")
        total_embeddings = embed_all_chunks(db)
        print(f"  Created {total_embeddings} embeddings")

        # Summary
        doc_count = db.query(Document).filter(Document.is_duplicate == False).count()
        print(f"\nTotal unique documents: {doc_count}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
