import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AppUser, Backlog, BacklogGame, IgdbGame
from app.features.auth.get_current_user import User
from app.features.backlog_game.add_backlog_game_handler import (
    AddBacklogGameHandler,
    AddBacklogGameRequest,
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


def test_handle_adds_new_game_to_backlog(db_session: Session):
    current_user = _create_user(db_session, "76561198000000000")
    backlog = Backlog(app_user_id=current_user.app_user_id)
    igdb_game = IgdbGame(igdb_game_id=1, name="New Game", total_rating=85.0)
    db_session.add_all([backlog, igdb_game])
    db_session.commit()

    request = AddBacklogGameRequest.model_validate({"gameId": 1})
    handler = AddBacklogGameHandler(db_session, current_user)

    actual = handler.handle(request)

    persisted = db_session.scalars(
        select(BacklogGame).where(BacklogGame.backlog_game_id == actual.backlog_game_id)
    ).one()
    assert persisted.backlog_id == backlog.backlog_id
    assert persisted.igdb_game_id == 1
    assert persisted.removed_on is None


def test_handle_reactivates_previously_removed_game(db_session: Session):
    current_user = _create_user(db_session, "76561198000000000")
    backlog = Backlog(app_user_id=current_user.app_user_id)
    igdb_game = IgdbGame(igdb_game_id=1, name="Return Game", total_rating=75.0)
    db_session.add_all([backlog, igdb_game])
    db_session.flush()

    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=1,
        removed_on="2026-04-10 12:00:00",
    )
    db_session.add(backlog_game)
    db_session.commit()

    request = AddBacklogGameRequest.model_validate({"gameId": 1})
    handler = AddBacklogGameHandler(db_session, current_user)

    actual = handler.handle(request)

    assert actual.backlog_game_id == backlog_game.backlog_game_id
    persisted = db_session.scalars(
        select(BacklogGame).where(
            BacklogGame.backlog_game_id == backlog_game.backlog_game_id
        )
    ).one()
    assert persisted.removed_on is None


def test_handle_raises_conflict_when_game_already_in_backlog(db_session: Session):
    current_user = _create_user(db_session, "76561198000000000")
    backlog = Backlog(app_user_id=current_user.app_user_id)
    igdb_game = IgdbGame(igdb_game_id=1, name="Conflict Game", total_rating=80.0)
    db_session.add_all([backlog, igdb_game])
    db_session.flush()

    backlog_game = BacklogGame(backlog_id=backlog.backlog_id, igdb_game_id=1)
    db_session.add(backlog_game)
    db_session.commit()

    request = AddBacklogGameRequest.model_validate({"gameId": 1})
    handler = AddBacklogGameHandler(db_session, current_user)

    with pytest.raises(HTTPException) as exc_info:
        handler.handle(request)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Game is already in your backlog."


def test_handle_raises_not_found_when_backlog_is_missing(db_session: Session):
    current_user = _create_user(db_session, "76561198000000000")
    request = AddBacklogGameRequest.model_validate({"gameId": 1})
    handler = AddBacklogGameHandler(db_session, current_user)

    with pytest.raises(HTTPException) as exc_info:
        handler.handle(request)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Backlog not found. Create one first."


def test_handle_raises_not_found_when_game_is_missing(db_session: Session):
    current_user = _create_user(db_session, "76561198000000000")
    backlog = Backlog(app_user_id=current_user.app_user_id)
    db_session.add(backlog)
    db_session.commit()

    request = AddBacklogGameRequest.model_validate({"gameId": 999})
    handler = AddBacklogGameHandler(db_session, current_user)

    with pytest.raises(HTTPException) as exc_info:
        handler.handle(request)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Game not found."
