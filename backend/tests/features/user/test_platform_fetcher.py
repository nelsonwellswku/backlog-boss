from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.models import IgdbGame, IgdbGamePlatform, IgdbPlatform
from app.features.user.platform_fetcher import PlatformFetcher


def _create_game(db_session: Session, igdb_game_id: int) -> IgdbGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=f"Game {igdb_game_id}",
        total_rating=80.0,
    )
    db_session.add(game)
    db_session.flush()
    return game


def _windows_platform(db_session: Session) -> IgdbPlatform:
    platform = db_session.get(IgdbPlatform, 6)
    if platform is None:
        platform = IgdbPlatform(igdb_platform_id=6, name="Windows")
        db_session.add(platform)
        db_session.flush()
    return platform


def test_fetch_updates_games_without_platforms(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 1)
    _create_game(db_session, 2)

    game_3 = _create_game(db_session, 3)
    win = _windows_platform(db_session)
    stmt = (
        select(IgdbGame)
        .where(IgdbGame.igdb_game_id == 3)
        .options(selectinload(IgdbGame.platforms))
    )
    game_3 = db_session.scalars(stmt).one()
    game_3.platforms.append(win)
    db_session.commit()

    igdb_client = mocker.Mock()
    igdb_client.get_platforms_by_game_ids.return_value = {
        1: [6, 14],
        2: [3],
    }

    fetcher = PlatformFetcher(db_session, igdb_client)
    fetcher.fetch_and_persist([1, 2, 3])

    platforms_1 = db_session.scalars(
        select(IgdbPlatform.igdb_platform_id)
        .join(IgdbGamePlatform)
        .where(IgdbGamePlatform.igdb_game_id == 1)
    ).all()
    platforms_2 = db_session.scalars(
        select(IgdbPlatform.igdb_platform_id)
        .join(IgdbGamePlatform)
        .where(IgdbGamePlatform.igdb_game_id == 2)
    ).all()
    platforms_3 = db_session.scalars(
        select(IgdbPlatform.igdb_platform_id)
        .join(IgdbGamePlatform)
        .where(IgdbGamePlatform.igdb_game_id == 3)
    ).all()

    assert sorted(platforms_1) == [6, 14]
    assert sorted(platforms_2) == [3]
    assert platforms_3 == [6]

    igdb_client.get_platforms_by_game_ids.assert_called_once_with([1, 2])


def test_fetch_skips_when_no_games_missing_platforms(
    db_session: Session,
    mocker: MockerFixture,
):
    game = _create_game(db_session, 1)
    win = _windows_platform(db_session)
    stmt = (
        select(IgdbGame)
        .where(IgdbGame.igdb_game_id == 1)
        .options(selectinload(IgdbGame.platforms))
    )
    game = db_session.scalars(stmt).one()
    game.platforms.append(win)
    db_session.commit()

    igdb_client = mocker.Mock()

    fetcher = PlatformFetcher(db_session, igdb_client)
    fetcher.fetch_and_persist([1])

    igdb_client.get_platforms_by_game_ids.assert_not_called()


def test_fetch_handles_empty_game_list(
    db_session: Session,
    mocker: MockerFixture,
):
    igdb_client = mocker.Mock()

    fetcher = PlatformFetcher(db_session, igdb_client)
    fetcher.fetch_and_persist([])

    igdb_client.get_platforms_by_game_ids.assert_not_called()
