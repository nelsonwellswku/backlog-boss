from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.features.auth.auth_router import auth_router
from app.features.health.health_router import health_router
from app.pages.home import home_page_router

app = FastAPI(
    title="Backlog Boss",
    docs_url="/api/docs",
    redoc_url=None,
    description="Prioritize your video game backlog",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(home_page_router, tags=["Page"])
app.include_router(health_router, tags=["Health"])
app.include_router(auth_router, tags=["Auth"])
