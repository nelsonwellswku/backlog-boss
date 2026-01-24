import json
from unittest.mock import Mock

from igdb.wrapper import IGDBWrapper

from app.infrastructure.igdb_client import IgdbClient, IgdbExternalGameDict, IgdbGame


def test_get_games_maps_steam_ids_to_igdb_games():
    mock_games: list[IgdbExternalGameDict] = [
        {
            "uid": "1",
            "game": {"id": 123, "name": "Super Mario Bros.", "total_rating": 95.5},
        },
        {
            "uid": "2",
            "game": {"id": 456, "name": "Legend of Zelda", "total_rating": 98.2},
        },
    ]
    mock_time_to_beats: list[dict] = [
        {"game_id": 123, "normally": 7200},
        {"game_id": 456, "normally": 10800},
    ]
    igdb_wrapper_mock = Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.side_effect = [
        json.dumps(mock_games).encode("utf-8"),
        json.dumps(mock_time_to_beats).encode("utf-8"),
    ]

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    actual = igdbClient.get_games(set([1, 2]), 2)

    expected = [
        IgdbGame(123, 1, "Super Mario Bros.", 95.5, 7200),
        IgdbGame(456, 2, "Legend of Zelda", 98.2, 10800),
    ]

    assert actual == expected


def test_get_games_selects_lowest_igdb_id_per_steam_game():
    mock_games: list[IgdbExternalGameDict] = [
        {
            "uid": "2362420",
            "game": {
                "id": 74,
                "name": "Mass Effect 2 (2010 Edition)",
                "total_rating": 94.5,
            },
        },
        {
            "uid": "24980",
            "game": {"id": 74, "name": "Mass Effect 2", "total_rating": 94.5},
        },
    ]
    mock_time_to_beats: list[dict] = [
        {"game_id": 74, "normally": 18000},
    ]
    igdb_wrapper_mock: IGDBWrapper = Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.side_effect = [
        json.dumps(mock_games).encode("utf-8"),
        json.dumps(mock_time_to_beats).encode("utf-8"),
    ]

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    actual = igdbClient.get_games(steam_ids=set([1, 2]), limit=3)

    expected = [
        IgdbGame(74, 24980, "Mass Effect 2", 94.5, 18000),
    ]

    assert actual == expected
