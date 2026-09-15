# Ganymede API — Backup and Restore

"""Backup and restore operations for disaster recovery.

Two backup paths:
1. pg_dump: logical backup (schema + data). Portable across PG versions.
2. Volume snapshot: physical backup of data directory. Faster restore.

Both are invoked from CLI/ops scripts, not from the running API.
This module provides Python wrappers for testability.
"""

import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def backup_database(
    db_url: str,
    backup_dir: str,
    filename: Optional[str] = None,
) -> str:
    """Create a pg_dump backup of the database.
    
    Args:
        db_url: PostgreSQL connection string
        backup_dir: Directory to store the backup file
        filename: Optional filename (default: ganymede_backup_YYYYMMDD_HHMMSS.sql)
    
    Returns:
        Path to the backup file
    """
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    if not filename:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"ganymede_backup_{timestamp}.sql"
    
    backup_file = backup_path / filename
    
    # pg_dump requires connection params parsed from URL
    # Using environment variable for password to avoid shell injection
    import re
    # postgresql+psycopg2://user:pass@host:port/dbname
    match = re.match(
        r"postgresql(?:\+psycopg2)?://(?:(?P<user>[^:@]+)(?::(?P<password>[^@]*))?@)?(?P<host>[^:/]+)(?::(?P<port>\d+)?)?/(?P<dbname>[^?]+)",
        db_url,
    )
    if not match:
        raise ValueError(f"Invalid PostgreSQL URL: {db_url}")
    
    user = match.group("user") or "postgres"
    password = match.group("password") or ""
    host = match.group("host") or "localhost"
    port = match.group("port") or "5432"
    dbname = match.group("dbname") or "ganymede"
    
    env = {
        **__import__("os").environ,
        "PGPASSWORD": password,
        "PGUSER": user,
        "PGHOST": host,
        "PGPORT": port,
        "PGDATABASE": dbname,
    }
    
    cmd = [
        "pg_dump",
        "--format=plain",
        "--clean",  # DROP before CREATE
        "--if-exists",
        "--no-owner",  # Don't include ownership commands
        "--no-privileges",  # Don't include privilege commands
        "-f", str(backup_file),
    ]
    
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {result.stderr}")
    
    logger.info(f"Database backed up to {backup_file}")
    return str(backup_file)


def restore_database(
    db_url: str,
    backup_file: str,
) -> None:
    """Restore a database from a pg_dump backup.
    
    Args:
        db_url: PostgreSQL connection string (target database)
        backup_file: Path to .sql backup file
    """
    import re
    match = re.match(
        r"postgresql(?:\+psycopg2)?://(?:(?P<user>[^:@]+)(?::(?P<password>[^@]*))?@)?(?P<host>[^:/]+)(?::(?P<port>\d+)?)?/(?P<dbname>[^?]+)",
        db_url,
    )
    if not match:
        raise ValueError(f"Invalid PostgreSQL URL: {db_url}")
    
    user = match.group("user") or "postgres"
    password = match.group("password") or ""
    host = match.group("host") or "localhost"
    port = match.group("port") or "5432"
    dbname = match.group("dbname") or "ganymede"
    
    env = {
        **__import__("os").environ,
        "PGPASSWORD": password,
        "PGUSER": user,
        "PGHOST": host,
        "PGPORT": port,
        "PGDATABASE": dbname,
    }
    
    cmd = [
        "psql",
        "--file", backup_file,
        "--echo-errors",
        "--set", "ON_ERROR_STOP=on",
    ]
    
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"psql restore failed: {result.stderr}")
    
    logger.info(f"Database restored from {backup_file}")
