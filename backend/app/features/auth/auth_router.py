from dataclasses import dataclass
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from httpx import QueryParams
import httpx
from steam_web_api import Steam

from app.settings import AppSettings


auth_router = APIRouter()


@dataclass
class OpenIdCallbackParams:
    ns: str | None = None
    mode: str | None = None
    op_endpoint: str | None = None
    claimed_id: str | None = None
    identity: str | None = None
    return_to: str | None = None
    response_nonce: str | None = None
    assoc_handle: str | None = None
    signed: str | None = None
    sig: str | None = None


def openid_callback_params(request: Request):
    qp = request.query_params
    return OpenIdCallbackParams(
        ns=qp.get("openid.ns"),
        mode=qp.get("openid.mode"),
        op_endpoint=qp.get("openid.op_endpoint"),
        claimed_id=qp.get("openid.claimed_id"),
        identity=qp.get("openid.identity"),
        return_to=qp.get("openid.return_to"),
        response_nonce=qp.get("openid.response_nonce"),
        assoc_handle=qp.get("openid.assoc_handle"),
        signed=qp.get("openid.signed"),
        sig=qp.get("openid.sig"),
    )


@auth_router.get("/api/auth/twitch")
def auth_with_twitch(settings: AppSettings):
    query_params: QueryParams = QueryParams(
        client_id=settings.twitch_client_id,
        client_secret=settings.twitch_client_secret,
        grant_type="client_credentials",
    )
    response = httpx.post("https://id.twitch.tv/oauth2/token", params=query_params)
    response_json = response.json()
    return {"expires_in": response_json["expires_in"]}


@auth_router.get("/api/auth/steam")
def auth_with_steam():
    return_url = "http://localhost:8000/api/auth/steam/callback"
    realm = "http://localhost:8000/"

    query_params: QueryParams = QueryParams(
        {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": return_url,
            "openid.realm": realm,
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }
    )

    redirect_url = f"https://steamcommunity.com/openid/login?{query_params.__str__()}"

    return RedirectResponse(url=redirect_url)


@auth_router.get("/api/auth/steam/callback")
def steam_callback(
    settings: AppSettings,
    query_params: OpenIdCallbackParams = Depends(openid_callback_params),
):
    outgoing_query_params: QueryParams = QueryParams(
        {
            "openid.ns": query_params.ns,
            "openid.op_endpoint": query_params.op_endpoint,
            "openid.claimed_id": query_params.claimed_id,
            "openid.identity": query_params.identity,
            "openid.return_to": query_params.return_to,
            "openid.response_nonce": query_params.response_nonce,
            "openid.assoc_handle": query_params.assoc_handle,
            "openid.signed": query_params.signed,
            "openid.sig": query_params.sig,
            "openid.mode": "check_authentication",
        }
    )

    check_auth_response = httpx.post(
        "https://steamcommunity.com/openid/login",
        params=outgoing_query_params,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if not "is_valid:true" in check_auth_response.text:
        raise ValueError("Log in is not valid.")

    steam = Steam(settings.steam_api_key)
    assert query_params.claimed_id
    claimed_id = query_params.claimed_id.split("/")[-1]
    assert claimed_id
    owned_games = steam.users.get_owned_games(claimed_id, include_appinfo=True, includ_free_games=False)

    return {"claimed_id": query_params.claimed_id, "owned_games": owned_games}
