from fastapi import FastAPI

from app.features.auth.auth_router import auth_router
from app.features.health.health_router import health_router

app = FastAPI(
    title="Backlog Boss",
    docs_url="/api/docs",
    redoc_url=None,
    description="Prioritize your video game backlog",
)

app.include_router(health_router, tags=["Health"])
app.include_router(auth_router, tags=["Auth"])
