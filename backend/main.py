import logging
from pathlib import Path

from app.features.auth.auth_router import auth_router
from app.features.health.health_router import health_router
from app.features.user.user_router import user_router
from app.http_client import configure_httpx_lifespan
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
assets_dir = static_dir / "assets"
if static_dir.exists():
    if assets_dir.exists():
        app.mount(
            "/assets", StaticFiles(directory=str(assets_dir)), name="assets"
        )

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """Serve the React SPA for all non-API routes"""
        file_path = (static_dir / full_path).resolve()
        static_dir_resolved = static_dir.resolve()

        # Ensure the resolved path is within the static directory
        try:
            file_path.relative_to(static_dir_resolved)
        except ValueError:
            # Path is outside static directory, return index.html
            return FileResponse(static_dir / "index.html")

        if file_path.is_file():
            return FileResponse(file_path)
        # For all other routes, return index.html (SPA fallback)
        return FileResponse(static_dir / "index.html")
