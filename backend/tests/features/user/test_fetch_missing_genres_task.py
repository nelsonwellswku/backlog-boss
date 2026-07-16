from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AppUser,
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
    IgdbGameGenre,
    IgdbGenre,
)
from app.features.user.fetch_missing_genres_task import (
    fetch_missing_genres_task,
)
from app.infrastructure.igdb_client import GenreResponse


def _create_app_user(db_session: Session) -> AppUser:
    app_user = AppUser(
        steam_id="76561198000000000",
        persona_name="Test Persona",
        first_name="Test",
        last_name="User",
    )
    db_session.add(app_user)
    db_session.flush()
    return app_user


def _create_backlog_game(
    db_session: Session,
    backlog: Backlog,
    igdb_game_id: int,
) -> BacklogGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=f"Game {igdb_game_id}",
        total_rating=80.0,
    )
    game.external_games.append(
        IgdbExternalGame(
            igdb_external_game_id=igdb_game_id + 1000,
            uid=igdb_game_id * 100,
            igdb_external_game_source_id=1,
        )
    )
    db_session.add(game)
    db_session.flush()

    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=game.igdb_game_id,
    )
    db_session.add(backlog_game)
    db_session.flush()
    return backlog_game


def test_fetch_missing_genres_updates_games_without_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()

    _create_backlog_game(db_session, backlog, 1)
    _create_backlog_game(db_session, backlog, 2)
    _create_backlog_game(db_session, backlog, 3)
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_genres_task.IgdbClient"
    )
    igdb_client_mock.create.return_value.get_genres_by_game_ids.return_value = {
        1: [GenreResponse(id=10, name="Action"), GenreResponse(id=20, name="RPG")],
        3: [GenreResponse(id=30, name="Strategy")],
    }

    fetch_missing_genres_task(backlog.backlog_id, db=db_session)

    genres_1 = db_session.scalars(
        select(IgdbGenre.igdb_genre_id)
        .join(IgdbGameGenre)
        .where(IgdbGameGenre.igdb_game_id == 1)
    ).all()
    genres_2 = db_session.scalars(
        select(IgdbGenre.igdb_genre_id)
        .join(IgdbGameGenre)
        .where(IgdbGameGenre.igdb_game_id == 2)
    ).all()
    genres_3 = db_session.scalars(
        select(IgdbGenre.igdb_genre_id)
        .join(IgdbGameGenre)
        .where(IgdbGameGenre.igdb_game_id == 3)
    ).all()

    assert sorted(genres_1) == [10, 20]
    assert genres_2 == []
    assert genres_3 == [30]


def test_fetch_missing_genres_skips_games_with_existing_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()

    game_1 = IgdbGame(
        igdb_game_id=1,
        name="Game 1",
        total_rating=80.0,
    )
    genre = IgdbGenre(igdb_genre_id=10, name="Action")
    db_session.add(genre)
    db_session.flush()
    game_1.genres.append(genre)
    db_session.add(game_1)
    db_session.flush()

    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=game_1.igdb_game_id,
    )
    db_session.add(backlog_game)
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_genres_task.IgdbClient"
    )

    fetch_missing_genres_task(backlog.backlog_id, db=db_session)

    igdb_client_mock.create.return_value.get_genres_by_game_ids.assert_not_called()


def test_fetch_missing_genres_handles_igdb_failure(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()

    _create_backlog_game(db_session, backlog, 1)
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_genres_task.IgdbClient"
    )
    igdb_client_mock.create.return_value.get_genres_by_game_ids.side_effect = Exception(
        "IGDB API error"
    )

    fetch_missing_genres_task(backlog.backlog_id, db=db_session)

    genres = db_session.scalars(
        select(IgdbGenre.igdb_genre_id)
        .join(IgdbGameGenre)
        .where(IgdbGameGenre.igdb_game_id == 1)
    ).all()
    assert genres == []


def test_fetch_missing_genres_empty_backlog(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_genres_task.IgdbClient"
    )

    fetch_missing_genres_task(backlog.backlog_id, db=db_session)

    igdb_client_mock.create.return_value.get_genres_by_game_ids.assert_not_called()
