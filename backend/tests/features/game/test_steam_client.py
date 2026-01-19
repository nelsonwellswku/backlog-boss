from unittest.mock import Mock

from steam_web_api import Steam

from app.features.game.steam_client import SteamClient, SteamGame


def test_get_owned_games_returns_steam_games():
    mock_response = {
        "games": [
            {"appid": 12345},
            {"appid": 67890},
        ]
    }
    steam_mock = Mock(spec=Steam)
    steam_mock.users.get_owned_games.return_value = mock_response

    steam_client = SteamClient(steam_mock)
    actual = steam_client.get_owned_games("76561197960287930")

    expected = [
        SteamGame(12345),
        SteamGame(67890),
    ]

    assert actual == expected


def test_get_owned_games_handles_missing_games_key():
    mock_response = {}
    steam_mock = Mock(spec=Steam)
    steam_mock.users.get_owned_games.return_value = mock_response

    steam_client = SteamClient(steam_mock)
    actual = steam_client.get_owned_games("76561197960287930")

    assert actual == []


def test_get_owned_games_handles_empty_games_list():
    mock_response = {"games": []}
    steam_mock = Mock(spec=Steam)
    steam_mock.users.get_owned_games.return_value = mock_response

    steam_client = SteamClient(steam_mock)
    actual = steam_client.get_owned_games("76561197960287930")

    assert actual == []
