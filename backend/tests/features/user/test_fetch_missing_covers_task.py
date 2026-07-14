from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AppUser,
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
)
from app.features.user.fetch_missing_covers_task import (
    fetch_missing_covers_task,
)


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
    cover_image_id: str | None = None,
) -> BacklogGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=f"Game {igdb_game_id}",
        total_rating=80.0,
        cover_image_id=cover_image_id,
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


def test_fetch_missing_covers_updates_games_without_covers(
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
        "app.features.user.fetch_missing_covers_task.IgdbClient"
    )
    igdb_client_mock.create.return_value.get_covers_by_game_ids.return_value = {
        1: "co1z2z",
        3: "co4abc",
    }

    fetch_missing_covers_task(backlog.backlog_id, db=db_session)

    game_1 = db_session.scalars(
        select(IgdbGame).where(IgdbGame.igdb_game_id == 1)
    ).one()
    game_2 = db_session.scalars(
        select(IgdbGame).where(IgdbGame.igdb_game_id == 2)
    ).one()
    game_3 = db_session.scalars(
        select(IgdbGame).where(IgdbGame.igdb_game_id == 3)
    ).one()

    assert game_1.cover_image_id == "co1z2z"
    assert game_2.cover_image_id is None
    assert game_3.cover_image_id == "co4abc"


def test_fetch_missing_covers_skips_games_with_existing_covers(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()

    _create_backlog_game(db_session, backlog, 1, cover_image_id="existing1")
    _create_backlog_game(db_session, backlog, 2, cover_image_id="existing2")
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_covers_task.IgdbClient"
    )

    fetch_missing_covers_task(backlog.backlog_id, db=db_session)

    igdb_client_mock.create.return_value.get_covers_by_game_ids.assert_not_called()


def test_fetch_missing_covers_handles_igdb_failure(
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
        "app.features.user.fetch_missing_covers_task.IgdbClient"
    )
    igdb_client_mock.create.return_value.get_covers_by_game_ids.side_effect = Exception(
        "IGDB API error"
    )

    fetch_missing_covers_task(backlog.backlog_id, db=db_session)

    game_1 = db_session.scalars(
        select(IgdbGame).where(IgdbGame.igdb_game_id == 1)
    ).one()
    assert game_1.cover_image_id is None


def test_fetch_missing_covers_empty_backlog(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_covers_task.IgdbClient"
    )

    fetch_missing_covers_task(backlog.backlog_id, db=db_session)

    igdb_client_mock.create.return_value.get_covers_by_game_ids.assert_not_called()
