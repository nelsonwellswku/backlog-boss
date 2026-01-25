import json

from igdb.wrapper import IGDBWrapper
from pytest_mock import MockerFixture

from app.infrastructure.igdb_client import (
    ExternalGame,
    ExternalGameSource,
    IgdbClient,
    IgdbGameResponse,
    TimeToBeatResponse,
)


def test_get_games_with_minimal_data_is_successful(mocker: MockerFixture):
    mock_games = [
        {
            "id": 1,
            "name": "Mockingbird Jam",
        },
    ]
    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    igdbClient.get_game_time_to_beats = mocker.Mock(return_value=[])

    actual = igdbClient.get_games(set([1]))

    expected = [IgdbGameResponse(id=1, name="Mockingbird Jam", external_games=[])]

    assert actual == expected


def test_get_games_with_complete_data_is_successful(mocker: MockerFixture):
    mock_games = [
        {
            "id": 1,
            "name": "The Legend of Zelda: Breath of the Wild",
            "total_rating": 97.5,
            "external_games": [
                {
                    "id": 100,
                    "game_id": 1,
                    "uid": "12345",
                    "external_game_source": {"id": 1},
                }
            ],
        },
    ]
    mock_time_to_beat = [TimeToBeatResponse(id=1, game_id=1, normally=18000)]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    igdbClient.get_game_time_to_beats = mocker.Mock(return_value=mock_time_to_beat)

    actual = igdbClient.get_games(set([12345]))

    expected = [
        IgdbGameResponse(
            id=1,
            name="The Legend of Zelda: Breath of the Wild",
            total_rating=97.5,
            external_games=[
                ExternalGame(
                    id=100, uid="12345", external_game_source=ExternalGameSource(id=1)
                )
            ],
            time_to_beat=18000,
        )
    ]

    assert actual == expected


def test_get_games_with_multiple_games_is_successful(mocker: MockerFixture):
    mock_games = [
        {
            "id": 1,
            "name": "Game One",
            "total_rating": 85.0,
            "external_games": [
                {"id": 100, "uid": "111", "external_game_source": {"id": 1}}
            ],
        },
        {
            "id": 2,
            "name": "Game Two",
            "total_rating": 90.0,
            "external_games": [
                {"id": 101, "uid": "222", "external_game_source": {"id": 1}}
            ],
        },
    ]
    mock_time_to_beat = [
        TimeToBeatResponse(id=1, game_id=1, normally=10000),
        TimeToBeatResponse(id=2, game_id=2, normally=15000),
    ]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    igdbClient.get_game_time_to_beats = mocker.Mock(return_value=mock_time_to_beat)

    actual = igdbClient.get_games(set([111, 222]))

    assert len(actual) == 2
    assert actual[0].id == 1
    assert actual[0].name == "Game One"
    assert actual[0].time_to_beat == 10000
    assert actual[1].id == 2
    assert actual[1].name == "Game Two"
    assert actual[1].time_to_beat == 15000


def test_get_games_filters_non_steam_external_games(mocker: MockerFixture):
    mock_games = [
        {
            "id": 1,
            "name": "Multi-Platform Game",
            "external_games": [
                {"id": 100, "uid": "111", "external_game_source": {"id": 1}},
                {"id": 101, "uid": "222", "external_game_source": {"id": 5}},
                {"id": 102, "uid": "333", "external_game_source": {"id": 10}},
            ],
        },
    ]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    igdbClient.get_game_time_to_beats = mocker.Mock(return_value=[])

    actual = igdbClient.get_games(set([111]))

    assert len(actual) == 1
    assert len(actual[0].external_games) == 1
    assert actual[0].external_games[0].external_game_source.id == 1


def test_get_games_returns_empty_list_when_no_games_found(mocker: MockerFixture):
    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps([]).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)

    actual = igdbClient.get_games(set([99999]))

    assert actual == []


def test_get_games_handles_missing_time_to_beat_data(mocker: MockerFixture):
    mock_games = [
        {
            "id": 1,
            "name": "Game Without Time To Beat",
            "external_games": [
                {"id": 100, "uid": "111", "external_game_source": {"id": 1}}
            ],
        },
    ]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    igdbClient.get_game_time_to_beats = mocker.Mock(return_value=[])

    actual = igdbClient.get_games(set([111]))

    assert len(actual) == 1
    assert actual[0].time_to_beat is None


def test_get_game_time_to_beats_is_successful(mocker: MockerFixture):
    mock_time_to_beat = [
        {"id": 1, "game_id": 10, "normally": 12000},
        {"id": 2, "game_id": 20, "normally": 25000},
    ]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_time_to_beat).encode(
        "utf-8"
    )

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)

    actual = igdbClient.get_game_time_to_beats([10, 20])

    expected = [
        TimeToBeatResponse(id=1, game_id=10, normally=12000),
        TimeToBeatResponse(id=2, game_id=20, normally=25000),
    ]

    assert actual == expected


def test_get_game_time_to_beats_returns_empty_list_when_no_data(mocker: MockerFixture):
    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps([]).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)

    actual = igdbClient.get_game_time_to_beats([999])

    assert actual == []
