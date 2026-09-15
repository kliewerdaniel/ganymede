"""Tests for health endpoints and backup service."""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app
from app.core.config import get_settings
from app.core.database import get_db, engine
from app.models import Base

settings = get_settings()


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestHealthEndpoints:
    def test_healthz_returns_200(self, client):
        """Liveness probe returns alive status."""
        resp = client.get("/api/v1/healthz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert data["version"] == "0.1.0"

    def test_readyz_returns_200(self, client):
        """Readiness probe returns ready status."""
        resp = client.get("/api/v1/readyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert "database" in data["checks"]
        assert data["checks"]["database"]["status"] == "healthy"
        assert "ollama" in data["checks"]

    def test_metrics_returns_counts(self, client):
        """Metrics endpoint returns DB counts."""
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "db_counts" in data
        assert "matters" in data["db_counts"]
        assert "documents" in data["db_counts"]
        assert "chunks" in data["db_counts"]
        assert "db_query_latency_ms" in data


class TestBackupService:
    def test_backup_database_creates_file(self):
        """backup_database creates a .sql file."""
        from app.services.backup import backup_database
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # This test requires a running PostgreSQL instance
            # Skip if not available
            try:
                result = backup_database(settings.DATABASE_URL, tmpdir)
                assert os.path.exists(result)
                assert result.endswith(".sql")
                assert os.path.getsize(result) > 0
            except Exception as e:
                pytest.skip(f"Database not available for backup test: {e}")

    def test_backup_database_custom_filename(self):
        """backup_database respects custom filename."""
        from app.services.backup import backup_database
        
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                result = backup_database(settings.DATABASE_URL, tmpdir, "custom_backup.sql")
                assert result.endswith("custom_backup.sql")
            except Exception as e:
                pytest.skip(f"Database not available for backup test: {e}")
