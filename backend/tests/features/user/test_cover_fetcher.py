from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from app.database.models import IgdbGame
from app.features.user.cover_fetcher import CoverFetcher


def _create_game(
    db_session: Session,
    igdb_game_id: int,
    cover_image_id: str | None = None,
) -> IgdbGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=f"Game {igdb_game_id}",
        total_rating=80.0,
        cover_image_id=cover_image_id,
    )
    db_session.add(game)
    db_session.flush()
    return game


def test_fetch_updates_games_without_covers(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 1)
    _create_game(db_session, 2)
    _create_game(db_session, 3, cover_image_id="existing")
    db_session.commit()

    igdb_client = mocker.Mock()
    igdb_client.get_covers_by_game_ids.return_value = {1: "co1z2z", 2: "co4abc"}

    fetcher = CoverFetcher(db_session, igdb_client)
    fetcher.fetch([1, 2, 3])

    game_1 = db_session.get(IgdbGame, 1)
    game_2 = db_session.get(IgdbGame, 2)
    game_3 = db_session.get(IgdbGame, 3)

    assert game_1.cover_image_id == "co1z2z"
    assert game_2.cover_image_id == "co4abc"
    assert game_3.cover_image_id == "existing"

    igdb_client.get_covers_by_game_ids.assert_called_once_with([1, 2])


def test_fetch_skips_when_no_games_missing_covers(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 1, cover_image_id="c1")
    _create_game(db_session, 2, cover_image_id="c2")
    db_session.commit()

    igdb_client = mocker.Mock()

    fetcher = CoverFetcher(db_session, igdb_client)
    fetcher.fetch([1, 2])

    igdb_client.get_covers_by_game_ids.assert_not_called()


def test_fetch_handles_empty_game_list(
    db_session: Session,
    mocker: MockerFixture,
):
    igdb_client = mocker.Mock()

    fetcher = CoverFetcher(db_session, igdb_client)
    fetcher.fetch([])

    igdb_client.get_covers_by_game_ids.assert_not_called()
