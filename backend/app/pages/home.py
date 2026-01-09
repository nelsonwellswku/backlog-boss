from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.pages.templates import templates

home_page_router = APIRouter()

@home_page_router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="base.html")

@home_page_router.get("/nested", response_class=HTMLResponse)
def nested(request: Request):
    return templates.TemplateResponse(request=request, name="nested/test.html")
