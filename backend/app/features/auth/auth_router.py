from fastapi import APIRouter
from httpx import QueryParams
import httpx

from app.settings import AppSettings


auth_router = APIRouter()


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
