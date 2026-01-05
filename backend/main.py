from fastapi import FastAPI

from app.features.health.health_router import health_router

app = FastAPI(
    title="Backlog Boss",
    description="Prioritize your video game backlog"
)

app.include_router(health_router, tags=["Health"])
