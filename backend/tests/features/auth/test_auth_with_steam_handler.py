from urllib.parse import parse_qs, urlsplit

from app.features.auth.auth_with_steam_handler import AuthWithSteamHandler
from app.settings import Settings


def test_handle_redirects_to_steam_openid_with_expected_query_params(
    dummy_settings: Settings,
):
    handler = AuthWithSteamHandler(dummy_settings)

    response = handler.handle()
    redirect_url = urlsplit(response.headers["location"])

    assert response.status_code == 307
    assert redirect_url.scheme == "https"
    assert redirect_url.netloc == "steamcommunity.com"
    assert redirect_url.path == "/openid/login"
    assert parse_qs(redirect_url.query) == {
        "openid.ns": ["http://specs.openid.net/auth/2.0"],
        "openid.mode": ["checkid_setup"],
        "openid.return_to": ["https://backlogboss.example.com/api/auth/steam/callback"],
        "openid.realm": ["https://backlogboss.example.com/"],
        "openid.identity": ["http://specs.openid.net/auth/2.0/identifier_select"],
        "openid.claimed_id": ["http://specs.openid.net/auth/2.0/identifier_select"],
    }
