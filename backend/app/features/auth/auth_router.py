from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import RedirectResponse

from app.features.auth.auth_with_steam_handler import AuthWithSteamHandler
from app.features.auth.logout_handler import LogoutHandler
from app.features.auth.steam_callback_handler import (
    OpenIdCallbackParams,
    SteamCallbackHandler,
)

auth_router = APIRouter(tags=["Auth"])


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


@auth_router.get(
    "/api/auth/logout",
    description="Logs the user out by invalidating their session and clearing the session cookie.",
)
def logout(handler: LogoutHandler = Depends()) -> Response:
    return handler.handle()
