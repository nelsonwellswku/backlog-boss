from datetime import datetime, timezone

from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    IgdbExternalGame,
    IgdbGame,
    IgdbGamePlatform,
    IgdbGenre,
    IgdbPlatform,
)
from app.features.game.persist_igdb_games import persist_igdb_games
from app.infrastructure.igdb_client import (
    CoverResponse,
    ExternalGameResponse,
    GenreResponse,
    IgdbGameResponse,
    PlatformResponse,
    TimeToBeatResponse,
)


def test_persist_igdb_games_returns_false_for_empty_list(
    db_session: Session,
):
    result = persist_igdb_games(db_session, [])

    assert result is False


def test_persist_igdb_games_skips_existing_games(
    db_session: Session,
    mocker: MockerFixture,
):
    existing = IgdbGame(
        igdb_game_id=1,
        name="Existing Game",
        total_rating=90.0,
        last_refreshed_at=datetime.now(tz=timezone.utc),
    )
    db_session.add(existing)
    db_session.flush()

    games = [
        IgdbGameResponse(
            id=1,
            name="Existing Game",
            total_rating=90.0,
        )
    ]

    result = persist_igdb_games(db_session, games)

    assert result is False
    assert db_session.scalars(select(IgdbGame)).all() == [existing]


def test_persist_igdb_games_persists_new_games(
    db_session: Session,
    mocker: MockerFixture,
):
    games = [
        IgdbGameResponse(
            id=100,
            name="New Game",
            total_rating=85.0,
            cover=CoverResponse(image_id="cover123"),
            time_to_beat=TimeToBeatResponse(id=200, game_id=100, normally=3600),
        )
    ]

    result = persist_igdb_games(db_session, games)

    assert result is True
    game = db_session.get(IgdbGame, 100)
    assert game is not None
    assert game.name == "New Game"
    assert game.total_rating == 85.0
    assert game.cover_image_id == "cover123"
    assert game.last_refreshed_at is not None  # noqa: E711


def test_persist_igdb_games_sets_last_refreshed_at(
    db_session: Session,
    mocker: MockerFixture,
):
    before = datetime.now(tz=timezone.utc)
    games = [
        IgdbGameResponse(
            id=300,
            name="Timestamp Game",
            total_rating=70.0,
        )
    ]

    persist_igdb_games(db_session, games)

    after = datetime.now(tz=timezone.utc)
    game = db_session.get(IgdbGame, 300)
    assert game is not None
    assert game.last_refreshed_at is not None  # noqa: E711
    assert before <= game.last_refreshed_at <= after


def test_persist_igdb_games_returns_false_when_no_new_games(
    db_session: Session,
    mocker: MockerFixture,
):
    existing = IgdbGame(
        igdb_game_id=5,
        name="Already Here",
        total_rating=80.0,
        last_refreshed_at=datetime.now(tz=timezone.utc),
    )
    db_session.add(existing)
    db_session.flush()

    games = [
        IgdbGameResponse(id=5, name="Already Here", total_rating=80.0),
        IgdbGameResponse(id=5, name="Already Here", total_rating=80.0),
    ]

    result = persist_igdb_games(db_session, games)

    assert result is False


def test_persist_igdb_games_creates_new_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    games = [
        IgdbGameResponse(
            id=400,
            name="Genre Game",
            total_rating=80.0,
            genres=[GenreResponse(id=500, name="Action")],
        )
    ]

    persist_igdb_games(db_session, games)

    genre = db_session.get(IgdbGenre, 500)
    assert genre is not None
    assert genre.name == "Action"


def test_persist_igdb_games_reuses_existing_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    genre = IgdbGenre(igdb_genre_id=501, name="RPG")
    db_session.add(genre)
    db_session.flush()

    games = [
        IgdbGameResponse(
            id=401,
            name="RPG Game",
            total_rating=80.0,
            genres=[GenreResponse(id=501, name="RPG")],
        )
    ]

    persist_igdb_games(db_session, games)

    genres = db_session.scalars(
        select(IgdbGenre).where(IgdbGenre.igdb_genre_id == 501)
    ).all()
    assert len(genres) == 1


def test_persist_igdb_games_creates_new_platforms(
    db_session: Session,
    mocker: MockerFixture,
):
    games = [
        IgdbGameResponse(
            id=402,
            name="Platform Game",
            total_rating=80.0,
            platforms=[PlatformResponse(id=6)],
        )
    ]

    persist_igdb_games(db_session, games)

    platform = db_session.get(IgdbPlatform, 6)
    assert platform is not None


def test_persist_igdb_games_filters_non_pc_platforms(
    db_session: Session,
    mocker: MockerFixture,
):
    games = [
        IgdbGameResponse(
            id=403,
            name="Console Game",
            total_rating=80.0,
            platforms=[PlatformResponse(id=49), PlatformResponse(id=6)],
        )
    ]

    persist_igdb_games(db_session, games)

    platform_ids = db_session.scalars(
        select(IgdbGamePlatform.igdb_platform_id).where(
            IgdbGamePlatform.igdb_game_id == 403
        )
    ).all()
    assert platform_ids == [6]


def test_persist_igdb_games_deduplicates_external_uids(
    db_session: Session,
    mocker: MockerFixture,
):
    games = [
        IgdbGameResponse(
            id=404,
            name="Game A",
            total_rating=80.0,
            external_games=[
                ExternalGameResponse(
                    id=600, game=404, uid="999", external_game_source=1
                )
            ],
        ),
        IgdbGameResponse(
            id=405,
            name="Game B",
            total_rating=80.0,
            external_games=[
                ExternalGameResponse(
                    id=601, game=405, uid="999", external_game_source=1
                )
            ],
        ),
    ]

    persist_igdb_games(db_session, games)

    external_games = db_session.scalars(
        select(IgdbExternalGame).where(IgdbExternalGame.uid == 999)
    ).all()
    assert len(external_games) == 1


def test_persist_igdb_games_skips_malformed_external_uids(
    db_session: Session,
    mocker: MockerFixture,
):
    games = [
        IgdbGameResponse(
            id=406,
            name="Malformed UID Game",
            total_rating=80.0,
            external_games=[
                ExternalGameResponse(
                    id=602, game=406, uid="abc,def", external_game_source=1
                )
            ],
        )
    ]

    persist_igdb_games(db_session, games)

    external_games = db_session.scalars(
        select(IgdbExternalGame).where(IgdbExternalGame.igdb_game_id == 406)
    ).all()
    assert len(external_games) == 0
