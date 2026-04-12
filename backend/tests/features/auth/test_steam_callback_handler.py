from datetime import datetime, timezone

import httpx
import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AppSession, AppUser
from app.features.auth.steam_callback_handler import (
    OpenIdCallbackParams,
    SteamCallbackHandler,
)
from app.infrastructure.steam_client import SteamUserDetails


def _build_openid_params() -> OpenIdCallbackParams:
    return OpenIdCallbackParams.model_validate(
        {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "id_res",
            "openid.op_endpoint": "https://steamcommunity.com/openid/login",
            "openid.claimed_id": (
                "https://steamcommunity.com/openid/id/76561198000000000"
            ),
            "openid.identity": "https://steamcommunity.com/openid/id/76561198000000000",
            "openid.return_to": "https://backlogboss.example.com/api/auth/steam/callback",
            "openid.response_nonce": "2026-04-12T00:00:00Zabcdef",
            "openid.assoc_handle": "1234567890",
            "openid.signed": "signed,op_endpoint,claimed_id,identity,return_to,response_nonce,assoc_handle",
            "openid.sig": "signature",
        }
    )


def test_handle_creates_user_session_and_redirects(
    db_session: Session,
    mocker: MockerFixture,
):
    steam_client = mocker.Mock()
    steam_client.get_user_details.return_value = SteamUserDetails(
        persona_name="Test Persona",
        real_name="Test User",
    )
    http_client = mocker.Mock()
    http_client.post.return_value = httpx.Response(
        200, text="ns:http://specs.openid.net/auth/2.0\nis_valid:true\n"
    )
    handler = SteamCallbackHandler(steam_client, http_client, db_session)

    response = handler.handle(_build_openid_params())

    user = db_session.scalars(select(AppUser)).one()
    app_session = db_session.scalars(select(AppSession)).one()

    assert response.status_code == 307
    assert response.headers["location"] == "/my-backlog"
    assert "session_key=" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    assert "Secure" in response.headers["set-cookie"]
    assert user.steam_id == "76561198000000000"
    assert user.persona_name == "Test Persona"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert app_session.app_user_id == user.app_user_id
    assert app_session.expiration_date > datetime.now(timezone.utc)
    steam_client.get_user_details.assert_called_once_with("76561198000000000")


def test_handle_raises_unauthorized_when_openid_verification_fails(
    db_session: Session,
    mocker: MockerFixture,
):
    steam_client = mocker.Mock()
    http_client = mocker.Mock()
    http_client.post.return_value = httpx.Response(
        200, text="ns:http://specs.openid.net/auth/2.0\nis_valid:false\n"
    )
    handler = SteamCallbackHandler(steam_client, http_client, db_session)

    with pytest.raises(HTTPException) as exc_info:
        handler.handle(_build_openid_params())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized"
    steam_client.get_user_details.assert_not_called()
