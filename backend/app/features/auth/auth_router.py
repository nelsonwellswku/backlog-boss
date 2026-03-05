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
from app.settings import AppSettings

auth_router = APIRouter()


class OpenIdCallbackParams(BaseModel):
    ns: str = Field(alias="openid.ns")
    mode: str = Field(alias="openid.mode")
    op_endpoint: str = Field(alias="openid.op_endpoint")
    claimed_id: str = Field(alias="openid.claimed_id")
    identity: str = Field(alias="openid.identity")
    return_to: str = Field(alias="openid.return_to")
    response_nonce: str = Field(alias="openid.response_nonce")
    assoc_handle: str = Field(alias="openid.assoc_handle")
    signed: str = Field(alias="openid.signed")
    sig: str = Field(alias="openid.sig")


@auth_router.get(
    "/api/auth/steam",
    description="Redirects the user to the Steam OpenID login page to begin the authentication process.",
)
def auth_with_steam(handler: AuthWithSteamHandler = Depends()) -> RedirectResponse:
    return handler.handle()


@auth_router.get("/api/auth/steam/callback")
def steam_callback(
    settings: AppSettings,
    db_session: DbSession,
    openid_params: Annotated[OpenIdCallbackParams, Query()],
):
    outgoing_query_params: QueryParams = QueryParams(
        {
            "openid.ns": openid_params.ns,
            "openid.op_endpoint": openid_params.op_endpoint,
            "openid.claimed_id": openid_params.claimed_id,
            "openid.identity": openid_params.identity,
            "openid.return_to": openid_params.return_to,
            "openid.response_nonce": openid_params.response_nonce,
            "openid.assoc_handle": openid_params.assoc_handle,
            "openid.signed": openid_params.signed,
            "openid.sig": openid_params.sig,
            "openid.mode": "check_authentication",
        }
    )

    check_auth_response = httpx.post(
        "https://steamcommunity.com/openid/login",
        params=outgoing_query_params,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if "is_valid:true" not in check_auth_response.text:
        raise ValueError("Log in is not valid.")

    assert openid_params.identity
    steam_id = openid_params.identity.split("/")[-1]

    steam = Steam(settings.steam_api_key)

    # create the user record if it doesn't already exist
    user_details = steam.users.get_user_details(steam_id)
    persona_name = user_details["player"]["personaname"]
    real_name = user_details["player"]["realname"]
    split_name = real_name.split(" ")
    first_name, last_name = split_name[1], split_name[-1]

    # start the user's session by creating a session in the database
    # and setting a session id cookie
    app_user = db_session.scalars(
        select(AppUser).where(AppUser.steam_id == steam_id)
    ).one_or_none()
    if app_user is None:
        app_user = AppUser(
            steam_id=steam_id,
            persona_name=persona_name,
            first_name=first_name,
            last_name=last_name,
        )
        db_session.add(app_user)
    else:
        app_user.persona_name = persona_name
        app_user.first_name = first_name
        app_user.last_name = last_name

    expiration = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    app_session = AppSession(app_user=app_user, expiration_date=expiration)
    db_session.add(app_session)

    db_session.flush()
    app_session_key = app_session.app_session_key

    db_session.commit()

    redirect = RedirectResponse("/my-backlog")
    redirect.set_cookie(
        "session_key", str(app_session_key), expires=expiration, secure=True
    )

    return redirect


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
