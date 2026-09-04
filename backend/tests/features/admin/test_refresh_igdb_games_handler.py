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
    current_user = mocker.Mock()
    current_user.app_user_id = 1
    handler = RefreshIgdbGamesHandler(db_session, current_user)

    response = handler.handle(background_tasks)

    assert isinstance(response, RefreshIgdbGamesResponse)
    assert response.status == "started"


def test_handle_schedules_background_task(
    db_session: Session,
    mocker: MockerFixture,
):
    background_tasks = mocker.Mock()
    current_user = mocker.Mock()
    current_user.app_user_id = 1
    handler = RefreshIgdbGamesHandler(db_session, current_user)

    handler.handle(background_tasks)

    background_tasks.add_task.assert_called_once()
    call_args = background_tasks.add_task.call_args
    # First positional arg should be a callable (job.run)
    assert callable(call_args[0][0])
    # Second positional arg should be the triggering user's id
    assert call_args[0][1] == 1
