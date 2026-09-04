from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from app.features.admin.refresh_igdb_games_handler import (
    RefreshIgdbGamesHandler,
    RefreshIgdbGamesResponse,
)


def test_handle_returns_started_response(
    db_session: Session,
    mocker: MockerFixture,
):
    background_tasks = mocker.Mock()
    handler = RefreshIgdbGamesHandler(db_session)

    response = handler.handle(background_tasks)

    assert isinstance(response, RefreshIgdbGamesResponse)
    assert response.status == "started"


def test_handle_schedules_background_task(
    db_session: Session,
    mocker: MockerFixture,
):
    background_tasks = mocker.Mock()
    handler = RefreshIgdbGamesHandler(db_session)

    handler.handle(background_tasks)

    background_tasks.add_task.assert_called_once()
    call_args = background_tasks.add_task.call_args
    # First positional arg should be a callable (job.run)
    assert callable(call_args[0][0])
