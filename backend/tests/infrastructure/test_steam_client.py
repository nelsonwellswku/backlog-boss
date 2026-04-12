from pytest_mock import MockerFixture

from app.infrastructure.steam_client import SteamClient, SteamGame, SteamUserDetails


def test_get_owned_games_returns_typed_games(mocker: MockerFixture):
    steam = mocker.Mock()
    steam.users.get_owned_games.return_value = {"games": [{"appid": 10}, {"appid": 20}]}
    client = SteamClient(steam)

    actual = client.get_owned_games("76561198000000000")

    assert actual == [SteamGame(steam_game_id=10), SteamGame(steam_game_id=20)]


def test_get_user_details_returns_typed_user_details(mocker: MockerFixture):
    steam = mocker.Mock()
    steam.users.get_user_details.return_value = {
        "player": {"personaname": "Test Persona", "realname": "Test User"}
    }
    client = SteamClient(steam)

    actual = client.get_user_details("76561198000000000")

    assert actual == SteamUserDetails(
        persona_name="Test Persona",
        real_name="Test User",
    )
