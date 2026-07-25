from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AppUser,
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
    IgdbGameTimeToBeat,
)
from app.features.auth.get_current_user import User
from app.features.user.refresh_my_backlog_handler import RefreshMyBacklogHandler
from app.infrastructure.igdb_client import (
    ExternalGameResponse,
    IgdbGameResponse,
    TimeToBeatResponse,
)
from app.infrastructure.steam_client import SteamGame


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


def _create_backlog(db_session: Session, current_user: User) -> Backlog:
    backlog = Backlog(app_user_id=current_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()
    return backlog


def _create_game(
    db_session: Session,
    igdb_game_id: int,
    name: str,
    steam_uid: int,
    total_rating: float | None = 90.0,
    time_to_beat: int | None = 3600,
) -> IgdbGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=name,
        total_rating=total_rating,
    )
    if time_to_beat is not None:
        game.time_to_beat = IgdbGameTimeToBeat(
            igdb_game_time_to_beat_id=igdb_game_id + 100,
            igdb_game_id=igdb_game_id,
            normally=time_to_beat,
        )
    game.external_games.append(
        IgdbExternalGame(
            igdb_external_game_id=igdb_game_id + 1000,
            uid=steam_uid,
            igdb_external_game_source_id=1,
        )
    )
    db_session.add(game)
    db_session.flush()
    return game


def test_handle_raises_not_found_when_backlog_is_missing(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    steam_client = mocker.Mock()
    igdb_client = mocker.Mock()
    handler = RefreshMyBacklogHandler(
        db_session,
        steam_client,
        current_user,
        igdb_client,
        mocker.Mock(),
        mocker.Mock(),
    )

    with pytest.raises(HTTPException) as exc_info:
        handler.handle()

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Backlog not found. Create one first."


def test_handle_returns_zero_when_no_new_games_to_add(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    backlog = _create_backlog(db_session, current_user)
    game = _create_game(db_session, 1, "Existing Game", 111)
    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=game.igdb_game_id,
    )
    db_session.add(backlog_game)
    db_session.commit()

    steam_client = mocker.Mock()
    steam_client.get_owned_games.return_value = [SteamGame(steam_game_id=111)]
    handler = RefreshMyBacklogHandler(
        db_session,
        steam_client,
        current_user,
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    )

    actual = handler.handle()

    assert actual.backlog_id == backlog.backlog_id
    assert actual.games_added_count == 0
    steam_client.get_owned_games.assert_called_once_with(current_user.steam_id)


def test_handle_adds_qualifying_new_game_skips_active_game(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    backlog = _create_backlog(db_session, current_user)
    existing_game = _create_game(db_session, 1, "Existing Game", 111)
    _create_game(db_session, 2, "New Game", 222)
    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=existing_game.igdb_game_id,
    )
    db_session.add(backlog_game)
    db_session.commit()

    steam_client = mocker.Mock()
    steam_client.get_owned_games.return_value = [
        SteamGame(steam_game_id=111),
        SteamGame(steam_game_id=222),
    ]
    cover_fetcher = mocker.Mock()
    genre_fetcher = mocker.Mock()
    handler = RefreshMyBacklogHandler(
        db_session,
        steam_client,
        current_user,
        mocker.Mock(),
        cover_fetcher,
        genre_fetcher,
    )

    actual = handler.handle()

    assert actual.backlog_id == backlog.backlog_id
    assert actual.games_added_count == 1

    backlog_game_ids = db_session.scalars(
        select(BacklogGame.igdb_game_id).where(
            BacklogGame.backlog_id == backlog.backlog_id
        )
    ).all()
    assert set(backlog_game_ids) == {1, 2}

    cover_fetcher.fetch_and_persist.assert_called_once()
    assert set(cover_fetcher.fetch_and_persist.call_args[0][0]) == {1, 2}
    genre_fetcher.fetch_and_persist.assert_called_once()
    assert set(genre_fetcher.fetch_and_persist.call_args[0][0]) == {1, 2}


def test_handle_raises_when_cover_fetcher_fails(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    backlog = _create_backlog(db_session, current_user)
    _create_game(db_session, 1, "Existing Game", 111)
    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=1,
    )
    db_session.add(backlog_game)
    db_session.commit()

    steam_client = mocker.Mock()
    steam_client.get_owned_games.return_value = [
        SteamGame(steam_game_id=111),
        SteamGame(steam_game_id=222),
    ]
    igdb_client = mocker.Mock()
    igdb_client.get_games_by_steam_id.return_value = [
        IgdbGameResponse(
            id=2,
            name="New Game",
            total_rating=85.0,
            external_games=[
                ExternalGameResponse(id=2001, game=2, uid="222", external_game_source=1)
            ],
            time_to_beat=TimeToBeatResponse(id=3001, game_id=2, normally=7200),
        ),
    ]
    cover_fetcher = mocker.Mock()
    cover_fetcher.fetch_and_persist.side_effect = RuntimeError("IGDB API error")
    genre_fetcher = mocker.Mock()
    handler = RefreshMyBacklogHandler(
        db_session,
        steam_client,
        current_user,
        igdb_client,
        cover_fetcher,
        genre_fetcher,
    )

    with pytest.raises(RuntimeError, match="IGDB API error"):
        handler.handle()

    db_session.rollback()

    backlog_game_ids = db_session.scalars(
        select(BacklogGame.igdb_game_id).where(
            BacklogGame.backlog_id == backlog.backlog_id
        )
    ).all()
    assert backlog_game_ids == [1]

    genre_fetcher.fetch_and_persist.assert_not_called()


def test_handle_skips_game_without_rating(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    backlog = _create_backlog(db_session, current_user)
    _create_game(
        db_session,
        1,
        "No Rating Game",
        111,
        total_rating=None,
        time_to_beat=3600,
    )
    db_session.commit()

    steam_client = mocker.Mock()
    steam_client.get_owned_games.return_value = [SteamGame(steam_game_id=111)]
    handler = RefreshMyBacklogHandler(
        db_session,
        steam_client,
        current_user,
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    )

    actual = handler.handle()

    assert actual.games_added_count == 0

    backlog_game_ids = db_session.scalars(
        select(BacklogGame.igdb_game_id).where(
            BacklogGame.backlog_id == backlog.backlog_id
        )
    ).all()
    assert len(backlog_game_ids) == 0


def test_handle_skips_game_without_time_to_beat(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    _create_backlog(db_session, current_user)
    _create_game(
        db_session,
        1,
        "No Time Game",
        111,
        total_rating=80.0,
        time_to_beat=None,
    )
    db_session.commit()

    steam_client = mocker.Mock()
    steam_client.get_owned_games.return_value = [SteamGame(steam_game_id=111)]
    handler = RefreshMyBacklogHandler(
        db_session,
        steam_client,
        current_user,
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    )

    actual = handler.handle()

    assert actual.games_added_count == 0


def test_handle_does_not_re_add_removed_game(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    backlog = _create_backlog(db_session, current_user)
    game = _create_game(db_session, 1, "Removed Game", 111)
    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=game.igdb_game_id,
        removed_on=datetime(2026, 4, 11, tzinfo=timezone.utc),
    )
    db_session.add(backlog_game)
    db_session.commit()

    steam_client = mocker.Mock()
    steam_client.get_owned_games.return_value = [SteamGame(steam_game_id=111)]
    handler = RefreshMyBacklogHandler(
        db_session,
        steam_client,
        current_user,
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    )

    actual = handler.handle()

    assert actual.games_added_count == 0

    backlog_game_ids = db_session.scalars(
        select(BacklogGame.igdb_game_id).where(
            BacklogGame.backlog_id == backlog.backlog_id
        )
    ).all()
    assert len(backlog_game_ids) == 1


def test_handle_fetches_new_igdb_games_and_adds_qualifying_ones(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    backlog = _create_backlog(db_session, current_user)
    existing_game = _create_game(db_session, 1, "Existing Game", 111)
    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=existing_game.igdb_game_id,
    )
    db_session.add(backlog_game)
    db_session.commit()

    steam_client = mocker.Mock()
    steam_client.get_owned_games.return_value = [
        SteamGame(steam_game_id=111),
        SteamGame(steam_game_id=222),
        SteamGame(steam_game_id=333),
    ]
    igdb_client = mocker.Mock()
    igdb_client.get_games_by_steam_id.return_value = [
        IgdbGameResponse(
            id=2,
            name="New Complete Game",
            total_rating=91.0,
            external_games=[
                ExternalGameResponse(
                    id=2001,
                    game=2,
                    uid="222",
                    external_game_source=1,
                ),
                ExternalGameResponse(
                    id=2002,
                    game=2,
                    uid="222,223",
                    external_game_source=1,
                ),
            ],
            time_to_beat=TimeToBeatResponse(id=3001, game_id=2, normally=7200),
        ),
        IgdbGameResponse(
            id=3,
            name="New Incomplete Game",
            total_rating=63.0,
            external_games=[
                ExternalGameResponse(id=2003, game=3, uid="333", external_game_source=1)
            ],
            time_to_beat=None,
        ),
    ]
    handler = RefreshMyBacklogHandler(
        db_session,
        steam_client,
        current_user,
        igdb_client,
        mocker.Mock(),
        mocker.Mock(),
    )

    actual = handler.handle()

    assert actual.backlog_id == backlog.backlog_id
    assert actual.games_added_count == 1

    igdb_client.get_games_by_steam_id.assert_called_once_with({222, 333})

    backlog_game_ids = db_session.scalars(
        select(BacklogGame.igdb_game_id).where(
            BacklogGame.backlog_id == backlog.backlog_id
        )
    ).all()
    assert set(backlog_game_ids) == {1, 2}
