# Ganymede API — FastAPI Application

"""FastAPI app factory."""

from fastapi import FastAPI
from app.api import router


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="Ganymede API",
        description="Private Matter Intelligence",
        version="0.1.0",
    )
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
