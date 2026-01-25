import json

from igdb.wrapper import IGDBWrapper
from pytest_mock import MockerFixture

from app.infrastructure.igdb_client import (
    ExternalGameResponse,
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
    mocker.patch.object(igdbClient, "get_external_games", return_value=[])
    mocker.patch.object(igdbClient, "get_game_time_to_beats", return_value=[])

    actual = igdbClient.get_games(set([1]))

    expected = [IgdbGameResponse(id=1, name="Mockingbird Jam", external_games=[])]

    assert actual == expected


def test_get_games_with_complete_data_is_successful(mocker: MockerFixture):
    mock_games = [
        {
            "id": 1,
            "name": "The Legend of Zelda: Breath of the Wild",
            "total_rating": 97.5,
        },
    ]
    mock_external_games = [
        ExternalGameResponse(id=100, game=1, uid="12345", external_game_source=1)
    ]
    mock_time_to_beat = [TimeToBeatResponse(id=1, game_id=1, normally=18000)]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    mocker.patch.object(
        igdbClient, "get_external_games", return_value=mock_external_games
    )
    mocker.patch.object(
        igdbClient, "get_game_time_to_beats", return_value=mock_time_to_beat
    )

    actual = igdbClient.get_games(set([12345]))

    expected = [
        IgdbGameResponse(
            id=1,
            name="The Legend of Zelda: Breath of the Wild",
            total_rating=97.5,
            external_games=[
                ExternalGameResponse(
                    id=100, game=1, uid="12345", external_game_source=1
                )
            ],
            time_to_beat=TimeToBeatResponse(id=1, game_id=1, normally=18000),
        )
    ]

    assert actual == expected


def test_get_games_with_multiple_games_is_successful(mocker: MockerFixture):
    mock_games = [
        {
            "id": 1,
            "name": "Game One",
            "total_rating": 85.0,
        },
        {
            "id": 2,
            "name": "Game Two",
            "total_rating": 90.0,
        },
    ]
    mock_external_games = [
        ExternalGameResponse(id=100, game=1, uid="111", external_game_source=1),
        ExternalGameResponse(id=101, game=2, uid="222", external_game_source=1),
    ]
    mock_time_to_beat = [
        TimeToBeatResponse(id=1, game_id=1, normally=10000),
        TimeToBeatResponse(id=2, game_id=2, normally=15000),
    ]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    mocker.patch.object(
        igdbClient, "get_external_games", return_value=mock_external_games
    )
    mocker.patch.object(
        igdbClient, "get_game_time_to_beats", return_value=mock_time_to_beat
    )

    actual = igdbClient.get_games(set([111, 222]))

    assert len(actual) == 2
    assert actual[0].id == 1
    assert actual[0].name == "Game One"
    assert actual[0].time_to_beat is not None
    assert actual[0].time_to_beat.normally == 10000
    assert actual[1].id == 2
    assert actual[1].name == "Game Two"
    assert actual[1].time_to_beat is not None
    assert actual[1].time_to_beat.normally == 15000


def test_get_games_filters_non_steam_external_games(mocker: MockerFixture):
    mock_games = [
        {
            "id": 1,
            "name": "Multi-Platform Game",
        },
    ]
    # Only Steam external game (source id 1) should be included
    mock_external_games = [
        ExternalGameResponse(id=100, game=1, uid="111", external_game_source=1),
    ]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    mocker.patch.object(
        igdbClient, "get_external_games", return_value=mock_external_games
    )
    mocker.patch.object(igdbClient, "get_game_time_to_beats", return_value=[])

    actual = igdbClient.get_games(set([111]))

    assert len(actual) == 1
    assert len(actual[0].external_games) == 1
    assert actual[0].external_games[0].external_game_source == 1


def test_get_games_returns_empty_list_when_no_games_found(mocker: MockerFixture):
    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps([]).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    # No need to mock get_external_games or get_game_time_to_beats since they won't be called

    actual = igdbClient.get_games(set([99999]))

    assert actual == []


def test_get_games_handles_missing_time_to_beat_data(mocker: MockerFixture):
    mock_games = [
        {
            "id": 1,
            "name": "Game Without Time To Beat",
        },
    ]
    mock_external_games = [
        ExternalGameResponse(id=100, game=1, uid="111", external_game_source=1)
    ]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_games).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)
    mocker.patch.object(
        igdbClient, "get_external_games", return_value=mock_external_games
    )
    mocker.patch.object(igdbClient, "get_game_time_to_beats", return_value=[])

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


def test_get_external_games_is_successful(mocker: MockerFixture):
    mock_external_games = [
        {"id": 100, "game": 1, "uid": "111", "external_game_source": 1},
        {"id": 101, "game": 2, "uid": "222", "external_game_source": 1},
    ]

    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps(mock_external_games).encode(
        "utf-8"
    )

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)

    actual = igdbClient.get_external_games([1, 2])

    expected = [
        ExternalGameResponse(id=100, game=1, uid="111", external_game_source=1),
        ExternalGameResponse(id=101, game=2, uid="222", external_game_source=1),
    ]

    assert actual == expected


def test_get_external_games_returns_empty_list_when_no_data(mocker: MockerFixture):
    igdb_wrapper_mock = mocker.Mock(spec=IGDBWrapper)
    igdb_wrapper_mock.api_request.return_value = json.dumps([]).encode("utf-8")

    igdbClient: IgdbClient = IgdbClient(igdb_wrapper_mock)

    actual = igdbClient.get_external_games([999])

    assert actual == []
