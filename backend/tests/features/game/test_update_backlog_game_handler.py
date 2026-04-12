from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AppUser, Backlog, BacklogGame, IgdbGame
from app.features.auth.get_current_user import User
from app.features.backlog_game.update_backlog_game_handler import (
    UpdateBacklogGameHandler,
    UpdateBacklogGameRequest,
)


def _create_user(db_session: Session, steam_id: str) -> User:
    app_user = AppUser(
        steam_id=steam_id,
        persona_name=f"Persona {steam_id[-2:]}",
        first_name="Test",
        last_name="User",
    )
    db_session.add(app_user)
    db_session.flush()

    return User(
        app_user_id=app_user.app_user_id,
        steam_id=app_user.steam_id,
        persona_name=app_user.persona_name,
        first_name=app_user.first_name,
        last_name=app_user.last_name,
    )


def test_handle_updates_backlog_game_dates(db_session: Session):
    current_user = _create_user(db_session, "76561198000000000")
    backlog = Backlog(app_user_id=current_user.app_user_id)
    igdb_game = IgdbGame(igdb_game_id=1, name="Update Me", total_rating=77.0)
    db_session.add_all([backlog, igdb_game])
    db_session.flush()

    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id, igdb_game_id=igdb_game.igdb_game_id
    )
    db_session.add(backlog_game)
    db_session.commit()

    completed_on = datetime(2026, 4, 12, tzinfo=timezone.utc)
    removed_on = datetime(2026, 4, 13, tzinfo=timezone.utc)
    request = UpdateBacklogGameRequest.model_validate(
        {"completedOn": completed_on, "removedOn": removed_on}
    )
    handler = UpdateBacklogGameHandler(db_session, current_user)

    actual = handler.handle(backlog_game.backlog_game_id, request)

    persisted = db_session.scalars(
        select(BacklogGame).where(
            BacklogGame.backlog_game_id == backlog_game.backlog_game_id
        )
    ).one()

    assert actual.backlog_game_id == backlog_game.backlog_game_id
    assert persisted.completed_on == completed_on
    assert persisted.removed_on == removed_on


def test_handle_raises_not_found_for_missing_backlog_game(db_session: Session):
    current_user = _create_user(db_session, "76561198000000000")
    request = UpdateBacklogGameRequest.model_validate(
        {"completedOn": None, "removedOn": None}
    )
    handler = UpdateBacklogGameHandler(db_session, current_user)

    with pytest.raises(HTTPException) as exc_info:
        handler.handle(9999, request)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Backlog game not found."


def test_handle_raises_unauthorized_for_other_users_backlog_game(db_session: Session):
    owner = _create_user(db_session, "76561198000000000")
    other_user = _create_user(db_session, "76561198000000001")
    backlog = Backlog(app_user_id=owner.app_user_id)
    igdb_game = IgdbGame(igdb_game_id=1, name="Protected Game", total_rating=77.0)
    db_session.add_all([backlog, igdb_game])
    db_session.flush()

    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id, igdb_game_id=igdb_game.igdb_game_id
    )
    db_session.add(backlog_game)
    db_session.commit()

    request = UpdateBacklogGameRequest.model_validate(
        {"completedOn": datetime(2026, 4, 12, tzinfo=timezone.utc), "removedOn": None}
    )
    handler = UpdateBacklogGameHandler(db_session, other_user)

    with pytest.raises(HTTPException) as exc_info:
        handler.handle(backlog_game.backlog_game_id, request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized"
