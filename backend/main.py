from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.features.auth.auth_router import auth_router
from app.features.health.health_router import health_router
from app.features.user.user_router import user_router
from app.http_client import configure_httpx_lifespan

import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Backlog Boss",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
    description="Prioritize your video game backlog",
    lifespan=configure_httpx_lifespan,
)

app.include_router(health_router, tags=["Health"])
app.include_router(auth_router, tags=["Auth"])
app.include_router(user_router, tags=["User"])

# Serve static files and SPA fallback (only if static directory exists)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for all non-API routes"""
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # For all other routes, return index.html (SPA fallback)
        return FileResponse(static_dir / "index.html")
