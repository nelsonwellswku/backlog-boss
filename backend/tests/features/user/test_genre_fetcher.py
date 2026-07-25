from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.models import IgdbGame, IgdbGameGenre, IgdbGenre
from app.features.user.genre_fetcher import GenreFetcher
from app.infrastructure.igdb_client import GenreResponse


def _create_game(db_session: Session, igdb_game_id: int) -> IgdbGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=f"Game {igdb_game_id}",
        total_rating=80.0,
    )
    db_session.add(game)
    db_session.flush()
    return game


def test_fetch_updates_games_without_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 1)
    _create_game(db_session, 2)

    game_3 = _create_game(db_session, 3)
    genre = IgdbGenre(igdb_genre_id=10, name="Action")
    db_session.add(genre)
    db_session.flush()
    stmt = (
        select(IgdbGame)
        .where(IgdbGame.igdb_game_id == 3)
        .options(selectinload(IgdbGame.genres))
    )
    game_3 = db_session.scalars(stmt).one()
    game_3.genres.append(genre)
    db_session.commit()

    igdb_client = mocker.Mock()
    igdb_client.get_genres_by_game_ids.return_value = {
        1: [GenreResponse(id=10, name="Action"), GenreResponse(id=20, name="RPG")],
        2: [GenreResponse(id=30, name="Strategy")],
    }

    fetcher = GenreFetcher(db_session, igdb_client)
    fetcher.fetch([1, 2, 3])

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
    assert sorted(genres_2) == [30]
    assert genres_3 == [10]

    igdb_client.get_genres_by_game_ids.assert_called_once_with([1, 2])


def test_fetch_skips_when_no_games_missing_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    game = _create_game(db_session, 1)
    genre = IgdbGenre(igdb_genre_id=10, name="Action")
    db_session.add(genre)
    db_session.flush()
    stmt = (
        select(IgdbGame)
        .where(IgdbGame.igdb_game_id == 1)
        .options(selectinload(IgdbGame.genres))
    )
    game = db_session.scalars(stmt).one()
    game.genres.append(genre)
    db_session.commit()

    igdb_client = mocker.Mock()

    fetcher = GenreFetcher(db_session, igdb_client)
    fetcher.fetch([1])

    igdb_client.get_genres_by_game_ids.assert_not_called()


def test_fetch_handles_empty_game_list(
    db_session: Session,
    mocker: MockerFixture,
):
    igdb_client = mocker.Mock()

    fetcher = GenreFetcher(db_session, igdb_client)
    fetcher.fetch([])

    igdb_client.get_genres_by_game_ids.assert_not_called()
