from fastapi import FastAPI

from app.features.auth.auth_router import auth_router
from app.features.game.game_router import game_router
from app.features.health.health_router import health_router
from app.features.user.user_router import user_router
from app.http_client import configure_httpx_lifespan

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
app.include_router(game_router, tags=["Game"])
