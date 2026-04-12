from datetime import datetime, timedelta, timezone
from logging import getLogger

import httpx
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from httpx import QueryParams
from pydantic import Field
from sqlalchemy import select
from steam_web_api import Steam

from app.database.engine import DbSession
from app.database.models import AppSession, AppUser
from app.features.api_model import ApiRequestModel
from app.settings import AppSettings


class OpenIdCallbackParams(ApiRequestModel):
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


class SteamCallbackHandler:
    def __init__(self, settings: AppSettings, db_session: DbSession) -> None:
        self.app_settings = settings
        self.db_session = db_session

    def handle(self, openid_params: "OpenIdCallbackParams"):
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
            "https://steamcommunity.com/openid/login", params=outgoing_query_params
        )
        if (
            not check_auth_response.is_success
            or "is_valid:true" not in check_auth_response.text
            or not openid_params.identity
        ):
            raise HTTPException(401, "Unauthorized")

        steam_id = openid_params.identity.split("/")[-1]

        steam = Steam(self.app_settings.steam_api_key)

        # create the user record if it doesn't already exist
        user_details = steam.users.get_user_details(steam_id)
        persona_name = user_details["player"]["personaname"]
        real_name = user_details["player"].get("realname", "")
        split_name = real_name.split(" ")
        first_name = split_name[0] if len(split_name) >= 1 else None
        last_name = split_name[-1] if len(split_name) >= 2 else None

        # start the user's session by creating a session in the database
        # and setting a session id cookie
        app_user = self.db_session.scalars(
            select(AppUser).where(AppUser.steam_id == steam_id)
        ).one_or_none()
        if app_user is None:
            app_user = AppUser(
                steam_id=steam_id,
                persona_name=persona_name,
                first_name=first_name,
                last_name=last_name,
            )
            self.db_session.add(app_user)
        else:
            app_user.persona_name = persona_name
            app_user.first_name = first_name
            app_user.last_name = last_name

        expiration = datetime.now(tz=timezone.utc) + timedelta(hours=1)
        app_session = AppSession(app_user=app_user, expiration_date=expiration)
        self.db_session.add(app_session)

        self.db_session.flush()
        app_session_key = app_session.app_session_key

        self.db_session.commit()

        redirect = RedirectResponse("/my-backlog")
        redirect.set_cookie(
            "session_key",
            str(app_session_key),
            expires=expiration,
            secure=True,
            httponly=True,
            samesite="lax",
        )

        return redirect
