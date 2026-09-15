# Ganymede API — FastAPI Application

"""FastAPI app factory."""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api import router
from app.core.cors import setup_cors


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="Ganymede API",
        description="Private Matter Intelligence",
        version="0.1.0",
    )

    # CORS
    setup_cors(app)

    # API routes
    app.include_router(router, prefix="/api/v1")
    from app.services.health import health_router
    app.include_router(health_router, prefix="/api/v1")

    # Static frontend — /web mount
    web_dir = "/web"
    if os.path.exists(web_dir) and os.path.exists(os.path.join(web_dir, "index.html")):
        app.mount("/static", StaticFiles(directory=web_dir), name="static")

        @app.get("/")
        def serve_frontend():
            index_path = os.path.join(web_dir, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return {"message": "Ganymede API — frontend not built"}

    return app


app = create_app()
