from datetime import datetime, timedelta, timezone
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from httpx import QueryParams
from pydantic import BaseModel, Field
from sqlalchemy import select
from steam_web_api import Steam

from app.database.engine import DbSession
from app.database.models import AppSession, AppUser
from app.features.auth.auth_with_steam_handler import AuthWithSteamHandler
from app.features.auth.steam_callback_handler import (
    OpenIdCallbackParams,
    SteamCallbackHandler,
)
from app.settings import AppSettings

auth_router = APIRouter()


@auth_router.get(
    "/api/auth/steam",
    description="Redirects the user to the Steam OpenID login page to begin the authentication process.",
)
def auth_with_steam(handler: AuthWithSteamHandler = Depends()) -> RedirectResponse:
    return handler.handle()


@auth_router.get(
    "/api/auth/steam/callback",
    description="Handles the Steam OpenID callback, verifies the authentication response, and creates a session for the user.",
)
def steam_callback(
    openid_params: Annotated[OpenIdCallbackParams, Query()],
    handler: SteamCallbackHandler = Depends(),
) -> RedirectResponse:
    return handler.handle(openid_params)


@auth_router.get("/api/auth/logout")
def logout(request: Request, db_session: DbSession):
    session_key = request.cookies.get("session_key")
    if session_key:
        app_session = db_session.scalars(
            select(AppSession).where(AppSession.app_session_key == session_key)
        ).one_or_none()
        if app_session:
            db_session.delete(app_session)
            db_session.commit()

    response = Response()
    response.delete_cookie("session_key")

    return response
