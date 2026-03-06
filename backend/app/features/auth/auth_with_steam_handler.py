from fastapi.datastructures import QueryParams
from fastapi.responses import RedirectResponse

from app.settings import AppSettings


class AuthWithSteamHandler:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def handle(self):
        return_url = f"{self.settings.base_url}/api/auth/steam/callback"
        realm = f"{self.settings.base_url}/"

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

        redirect_url = f"https://steamcommunity.com/openid/login?{str(query_params)}"

        return RedirectResponse(url=redirect_url)
