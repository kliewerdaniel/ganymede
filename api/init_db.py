# Ganymede API — Initialize database tables

"""Create all tables and extensions. Run once at startup."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.models import Base

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

# Create extensions
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()

# Drop all tables with CASCADE to handle foreign key dependencies
with engine.connect() as conn:
    conn.execute(text("""
        DROP TABLE IF EXISTS chunk_embeddings CASCADE;
        DROP TABLE IF EXISTS ingestion_jobs CASCADE;
        DROP TABLE IF EXISTS chunks CASCADE;
        DROP TABLE IF EXISTS pages CASCADE;
        DROP TABLE IF EXISTS documents CASCADE;
        DROP TABLE IF EXISTS matter_memberships CASCADE;
        DROP TABLE IF EXISTS matters CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        DROP TABLE IF EXISTS tenants CASCADE;
    """))
    conn.commit()

# Create tables
Base.metadata.create_all(engine)

print("Database initialized: extensions (uuid-ossp, vector) and all tables created.")
