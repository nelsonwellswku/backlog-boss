from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.models import AppUser, Backlog, BacklogGame, IgdbGame, IgdbGameTimeToBeat
from app.features.auth.get_current_user import User
from app.features.user.get_my_backlog_handler import GetMyBacklogHandler


def _create_current_user(db_session: Session) -> User:
    app_user = AppUser(
        steam_id="76561198000000000",
        persona_name="Test Persona",
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


def test_handle_returns_backlog_games_excluding_removed_entries(db_session: Session):
    current_user = _create_current_user(db_session)
    backlog = Backlog(app_user_id=current_user.app_user_id)
    game_with_time = IgdbGame(igdb_game_id=1, name="Keep Me", total_rating=90.0)
    game_with_time.time_to_beat = IgdbGameTimeToBeat(
        igdb_game_time_to_beat_id=101,
        igdb_game_id=1,
        normally=5400,
    )
    game_without_time = IgdbGame(igdb_game_id=2, name="No Time", total_rating=70.0)
    removed_game = IgdbGame(igdb_game_id=3, name="Removed", total_rating=50.0)
    db_session.add_all([backlog, game_with_time, game_without_time, removed_game])
    db_session.flush()

    completed_on = datetime(2026, 4, 12, tzinfo=timezone.utc)
    db_session.add_all(
        [
            BacklogGame(
                backlog_id=backlog.backlog_id,
                igdb_game_id=1,
                completed_on=completed_on,
            ),
            BacklogGame(backlog_id=backlog.backlog_id, igdb_game_id=2),
            BacklogGame(
                backlog_id=backlog.backlog_id,
                igdb_game_id=3,
                removed_on=datetime(2026, 4, 11, tzinfo=timezone.utc),
            ),
        ]
    )
    db_session.commit()

    actual = GetMyBacklogHandler(db_session, current_user).handle()

    rows = sorted(actual.games, key=lambda game: game.game_id)

    assert actual.backlog_id == backlog.backlog_id
    assert [(row.game_id, row.title, row.time_to_beat, row.completed_on) for row in rows] == [
        (1, "Keep Me", 5400, completed_on),
        (2, "No Time", None, None),
    ]


def test_handle_raises_not_found_when_backlog_is_missing(db_session: Session):
    current_user = _create_current_user(db_session)
    handler = GetMyBacklogHandler(db_session, current_user)

    with pytest.raises(HTTPException) as exc_info:
        handler.handle()

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Backlog not found."
