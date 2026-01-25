import json

from igdb.wrapper import IGDBWrapper
from pytest_mock import MockerFixture

from app.infrastructure.igdb_client import IgdbClient, IgdbGameResponse


def test_get_games_with_minimal_data_is_successful(mocker: MockerFixture):
    mock_games = [
        {
            "id": "1",
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
