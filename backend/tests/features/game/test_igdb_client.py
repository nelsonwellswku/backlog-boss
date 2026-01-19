import json
from unittest.mock import Mock

from igdb.wrapper import IGDBWrapper

from app.features.game.igdb_client import IgdbClient, IgdbExternalGameDict, IgdbGame


def test_get_games_returns_successfully():
    mock_games: list[IgdbExternalGameDict] = [
        {"uid": "1", "game": {"id": 123, "name": "Super Mario Bros."}},
        {"uid": "2", "game": {"id": 456, "name": "Legend of Zelda"}},
    ]
    igdb_wrapper_mock = Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    actual = igdbClient.get_games([1, 2], 2)

    expected = [
        IgdbGame(123, 1, "Super Mario Bros."),
        IgdbGame(456, 2, "Legend of Zelda"),
    ]

    assert actual == expected


def test_games_returns_lowest_igdb_id_game_when_there_are_multiple_igdb_games_for_a_single_steam_game():
    mock_games: list[IgdbExternalGameDict] = [
        {"uid": "1", "game": {"id": 123, "name": "Super Mario Bros. (revision 1)"}},
        {"uid": "2", "game": {"id": 456, "name": "Legend of Zelda"}},
        {"uid": "1", "game": {"id": 99, "name": "Super Mario Bros."}},
    ]
    igdb_wrapper_mock = Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    actual = igdbClient.get_games([1, 2], 2)

    expected = [
        IgdbGame(123, 1, "Super Mario Bros."),
        IgdbGame(456, 2, "Legend of Zelda"),
    ]

    assert actual == expected
