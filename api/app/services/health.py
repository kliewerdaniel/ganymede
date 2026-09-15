# Ganymede API — Health and Readiness Checks

"""Health and readiness endpoints for monitoring and chaos testing."""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db, engine

logger = logging.getLogger(__name__)

health_router = APIRouter()


@health_router.get("/healthz")
def healthz():
    """Liveness probe. Returns 200 if the process is alive."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
    }


@health_router.get("/readyz")
def readyz(db: Session = Depends(get_db)):
    """Readiness probe. Returns 200 if DB and Ollama are reachable."""
    checks = {}
    overall_healthy = True

    # DB check
    t0 = time.time()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "healthy",
            "latency_ms": round((time.time() - t0) * 1000, 1),
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round((time.time() - t0) * 1000, 1),
        }
        overall_healthy = False

    # Ollama check
    t0 = time.time()
    try:
        import requests
        from app.core.config import get_settings
        settings = get_settings()
        resp = requests.get(
            f"{settings.OLLAMA_URL}/api/tags",
            timeout=5,
        )
        checks["ollama"] = {
            "status": "healthy" if resp.status_code == 200 else "degraded",
            "latency_ms": round((time.time() - t0) * 1000, 1),
            "models_count": len(resp.json().get("models", [])) if resp.status_code == 200 else 0,
        }
    except Exception as e:
        checks["ollama"] = {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": round((time.time() - t0) * 1000, 1),
        }
        overall_healthy = False

    status_code = 200 if overall_healthy else 503
    return {
        "status": "ready" if overall_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


@health_router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    """System metrics and capacity indicators."""
    from app.models import Matter, Document, Chunk, ChunkEmbedding, User, AuditLog

    # DB counts
    t0 = time.time()
    db_counts = {}
    for name, model in [
        ("matters", Matter),
        ("documents", Document),
        ("chunks", Chunk),
        ("embeddings", ChunkEmbedding),
        ("users", User),
        ("audit_logs", AuditLog),
    ]:
        db_counts[name] = db.query(model).count()
    db_latency = round((time.time() - t0) * 1000, 1)

    # Storage size
    t0 = time.time()
    try:
        storage_size = db.execute(text(
            "SELECT pg_database_size(current_database())"
        )).scalar()
        storage_mb = round(storage_size / (1024 * 1024), 2)
    except Exception:
        storage_mb = None
    storage_latency = round((time.time() - t0) * 1000, 1)

    # Ollama model sizes
    ollama_info = {}
    try:
        import requests
        from app.core.config import get_settings
        settings = get_settings()
        resp = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            ollama_info = {
                "models": [
                    {"name": m["name"], "size_mb": round(m.get("size", 0) / (1024 * 1024), 1)}
                    for m in resp.json().get("models", [])
                ]
            }
    except Exception:
        pass

    return {
        "db_counts": db_counts,
        "db_query_latency_ms": db_latency,
        "storage": {
            "database_mb": storage_mb,
            "query_latency_ms": storage_latency,
        },
        "ollama": ollama_info,
        "timestamp": datetime.utcnow().isoformat(),
    }
