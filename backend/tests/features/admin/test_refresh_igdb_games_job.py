from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.models import (
    AppUser,
    IgdbExternalGame,
    IgdbGame,
    IgdbGameGenre,
    IgdbGamePlatform,
    IgdbGameTimeToBeat,
    IgdbGenre,
    IgdbPlatform,
    IgdbRefreshLock,
)
from app.features.admin.refresh_igdb_games_job import (
    LOCK_ID,
    RefreshIgdbGamesJob,
)
from app.features.admin.igdb_game_updater import IgdbGameUpdater
from app.infrastructure.igdb_client import ExternalGameResponse, GenreResponse


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


def _create_game(
    db_session: Session,
    game_id: int,
    last_refreshed_at: datetime | None = None,
) -> IgdbGame:
    game = IgdbGame(
        igdb_game_id=game_id,
        name=f"Game {game_id}",
        total_rating=80.0,
        last_refreshed_at=last_refreshed_at
        or datetime(2000, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(game)
    db_session.flush()
    return game


def _create_lock(
    db_session: Session,
    app_user: AppUser,
    last_updated_on: datetime,
    started_on: datetime | None = None,
) -> None:
    lock = IgdbRefreshLock(
        lock_id=LOCK_ID,
        started_on=started_on or last_updated_on,
        last_updated_on=last_updated_on,
        app_user_id=app_user.app_user_id,
    )
    db_session.add(lock)
    db_session.flush()


@contextmanager
def _fake_db_session(session: Session):
    yield session


def _load_game_with_time_to_beat(db_session: Session, game_id: int) -> IgdbGame:
    """Load a game with eagerly loaded time_to_beat relationship."""
    return db_session.scalars(
        select(IgdbGame)
        .where(IgdbGame.igdb_game_id == game_id)
        .options(joinedload(IgdbGame.time_to_beat))
    ).one()


# --- _acquire_lock tests ---


def test_acquire_lock_creates_lock_when_none_exists(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    job = RefreshIgdbGamesJob()

    result = job._acquire_lock(db_session, app_user.app_user_id)

    assert result is True
    lock = db_session.scalars(
        select(IgdbRefreshLock).where(IgdbRefreshLock.lock_id == LOCK_ID)
    ).one()
    assert lock.app_user_id == app_user.app_user_id


def test_acquire_lock_returns_false_when_lock_exists_and_is_fresh(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    _create_lock(db_session, app_user, last_updated_on=datetime.now(tz=timezone.utc))
    job = RefreshIgdbGamesJob()

    result = job._acquire_lock(db_session, app_user.app_user_id)

    assert result is False


def test_acquire_lock_takes_over_stale_lock(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    stale_time = datetime.now(tz=timezone.utc) - timedelta(minutes=10)
    _create_lock(db_session, app_user, last_updated_on=stale_time)
    job = RefreshIgdbGamesJob()

    result = job._acquire_lock(db_session, app_user.app_user_id)

    assert result is True
    lock = db_session.scalars(
        select(IgdbRefreshLock).where(IgdbRefreshLock.lock_id == LOCK_ID)
    ).one()
    assert lock.last_updated_on > stale_time
    assert lock.app_user_id == app_user.app_user_id


# --- _release_lock tests ---


def test_release_lock_deletes_lock_row(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    _create_lock(db_session, app_user, last_updated_on=datetime.now(tz=timezone.utc))
    job = RefreshIgdbGamesJob()

    job._release_lock(db_session)

    lock = db_session.scalars(
        select(IgdbRefreshLock).where(IgdbRefreshLock.lock_id == LOCK_ID)
    ).one_or_none()
    assert lock is None


# --- _get_stale_game_ids tests ---


def test_get_stale_game_ids_returns_games_with_old_last_refreshed_at(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(
        db_session,
        1,
        last_refreshed_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
    )
    job = RefreshIgdbGamesJob()

    ids = job._get_stale_game_ids(db_session)

    assert 1 in ids


def test_get_stale_game_ids_returns_games_older_than_30_days(
    db_session: Session,
    mocker: MockerFixture,
):
    old_date = datetime.now(tz=timezone.utc) - timedelta(days=31)
    _create_game(db_session, 2, last_refreshed_at=old_date)
    job = RefreshIgdbGamesJob()

    ids = job._get_stale_game_ids(db_session)

    assert 2 in ids


def test_get_stale_game_ids_excludes_recently_refreshed_games(
    db_session: Session,
    mocker: MockerFixture,
):
    recent = datetime.now(tz=timezone.utc) - timedelta(days=5)
    _create_game(db_session, 3, last_refreshed_at=recent)
    job = RefreshIgdbGamesJob()

    ids = job._get_stale_game_ids(db_session)

    assert 3 not in ids


# --- update_batch tests ---


def test_update_batch_updates_cover_and_refreshed_at(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 10, last_refreshed_at=datetime.now(tz=timezone.utc))
    now = datetime.now(tz=timezone.utc)

    IgdbGameUpdater(db_session).update_batch(
        [10],
        covers={10: "abc123"},
        genres={},
        platforms={},
        time_to_beats={},
        now=now,
    )

    game = db_session.get(IgdbGame, 10)
    assert game is not None
    assert game.cover_image_id == "abc123"
    assert game.last_refreshed_at == now


def test_update_batch_creates_time_to_beat_when_missing(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 11)
    now = datetime.now(tz=timezone.utc)

    IgdbGameUpdater(db_session).update_batch(
        [11],
        covers={},
        genres={},
        platforms={},
        time_to_beats={11: 3600},
        now=now,
    )

    ttb = db_session.scalars(
        select(IgdbGameTimeToBeat).where(IgdbGameTimeToBeat.igdb_game_id == 11)
    ).one()
    assert ttb.normally == 3600


def test_update_batch_updates_existing_time_to_beat(
    db_session: Session,
    mocker: MockerFixture,
):
    game = _create_game(db_session, 12)
    game.time_to_beat = IgdbGameTimeToBeat(
        igdb_game_time_to_beat_id=12,
        igdb_game_id=12,
        normally=1000,
    )
    db_session.flush()
    now = datetime.now(tz=timezone.utc)

    IgdbGameUpdater(db_session).update_batch(
        [12],
        covers={},
        genres={},
        platforms={},
        time_to_beats={12: 5000},
        now=now,
    )

    loaded_game = _load_game_with_time_to_beat(db_session, 12)
    assert loaded_game.time_to_beat is not None
    assert loaded_game.time_to_beat.normally == 5000


def test_update_batch_replaces_genre_associations(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 13)
    existing_genre = IgdbGenre(igdb_genre_id=100, name="Existing Genre")
    db_session.add(existing_genre)
    db_session.flush()
    db_session.add(IgdbGameGenre(igdb_game_id=13, igdb_genre_id=100))
    db_session.flush()
    now = datetime.now(tz=timezone.utc)
    genre_data = GenreResponse(id=100, name="Existing Genre")

    IgdbGameUpdater(db_session).update_batch(
        [13],
        covers={},
        genres={13: [genre_data]},
        platforms={},
        time_to_beats={},
        now=now,
    )

    genre_ids = db_session.scalars(
        select(IgdbGameGenre.igdb_genre_id).where(IgdbGameGenre.igdb_game_id == 13)
    ).all()
    assert genre_ids == [100]


def test_update_batch_creates_new_genre_when_missing(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 14)
    now = datetime.now(tz=timezone.utc)
    genre_data = GenreResponse(id=200, name="New Genre")

    IgdbGameUpdater(db_session).update_batch(
        [14],
        covers={},
        genres={14: [genre_data]},
        platforms={},
        time_to_beats={},
        now=now,
    )

    db_session.flush()
    genre = db_session.get(IgdbGenre, 200)
    assert genre is not None
    assert genre.name == "New Genre"
    genre_ids = db_session.scalars(
        select(IgdbGameGenre.igdb_genre_id).where(IgdbGameGenre.igdb_game_id == 14)
    ).all()
    assert genre_ids == [200]


def test_update_batch_replaces_platform_associations(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 15)
    # Platforms 6 (Windows) and 14 (Mac) are seeded by migration 0011,
    # so only the association row needs creating here.
    db_session.add(IgdbGamePlatform(igdb_game_id=15, igdb_platform_id=6))
    db_session.flush()
    now = datetime.now(tz=timezone.utc)

    IgdbGameUpdater(db_session).update_batch(
        [15],
        covers={},
        genres={},
        platforms={15: [14]},
        time_to_beats={},
        now=now,
    )

    platform_ids = db_session.scalars(
        select(IgdbGamePlatform.igdb_platform_id).where(
            IgdbGamePlatform.igdb_game_id == 15
        )
    ).all()
    assert platform_ids == [14]


def test_update_batch_skips_unknown_platform_when_missing(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 16)
    now = datetime.now(tz=timezone.utc)

    # Platform 48 is not in the migration-seeded set (6, 14, 3).
    IgdbGameUpdater(db_session).update_batch(
        [16],
        covers={16: "abc"},
        genres={},
        platforms={16: [48]},
        time_to_beats={},
        now=now,
    )

    assert db_session.get(IgdbPlatform, 48) is None
    platform_ids = db_session.scalars(
        select(IgdbGamePlatform.igdb_platform_id).where(
            IgdbGamePlatform.igdb_game_id == 16
        )
    ).all()
    assert platform_ids == []


def test_update_batch_skips_when_game_not_found(
    db_session: Session,
    mocker: MockerFixture,
):
    now = datetime.now(tz=timezone.utc)

    IgdbGameUpdater(db_session).update_batch(
        [99999],
        covers={99999: "abc"},
        genres={99999: [GenreResponse(id=1, name="G")]},
        platforms={99999: [6]},
        time_to_beats={99999: 100},
        now=now,
    )

    assert db_session.get(IgdbGame, 99999) is None


def test_update_batch_updates_multiple_games_with_mixed_payloads(
    db_session: Session,
    mocker: MockerFixture,
):
    stale = datetime(2000, 1, 1, tzinfo=timezone.utc)
    _create_game(db_session, 20, last_refreshed_at=stale)
    _create_game(db_session, 21, last_refreshed_at=stale)
    _create_game(db_session, 22, last_refreshed_at=stale)
    db_session.add(
        IgdbExternalGame(
            igdb_external_game_id=2001,
            uid=111,
            igdb_game_id=20,
            igdb_external_game_source_id=1,
            year=2019,
        )
    )
    db_session.flush()
    now = datetime.now(tz=timezone.utc)

    IgdbGameUpdater(db_session).update_batch(
        [20, 21, 22, 99998],
        covers={20: "cover20", 21: "cover21"},
        genres={20: [GenreResponse(id=300, name="Batch Genre")]},
        platforms={21: [6]},
        time_to_beats={20: 1000, 21: 2000},
        now=now,
        externals={
            20: [
                ExternalGameResponse(
                    id=2001, game=20, uid="111", external_game_source=1, year=2024
                )
            ]
        },
        ratings={20: 88.5},
    )

    game20 = db_session.get(IgdbGame, 20)
    assert game20 is not None
    assert game20.cover_image_id == "cover20"
    assert game20.total_rating == 88.5
    assert game20.last_refreshed_at == now
    game21 = db_session.get(IgdbGame, 21)
    assert game21 is not None
    assert game21.cover_image_id == "cover21"
    assert game21.last_refreshed_at == now
    # Game 22 has no payload data: last_refreshed_at stays stale for retry.
    game22 = db_session.get(IgdbGame, 22)
    assert game22 is not None
    assert game22.last_refreshed_at == stale

    ttb_rows = db_session.execute(
        select(IgdbGameTimeToBeat.igdb_game_id, IgdbGameTimeToBeat.normally).where(
            IgdbGameTimeToBeat.igdb_game_id.in_([20, 21])
        )
    ).all()
    ttb_values = {row[0]: row[1] for row in ttb_rows}
    assert ttb_values == {20: 1000, 21: 2000}

    genre_ids = db_session.scalars(
        select(IgdbGameGenre.igdb_genre_id).where(IgdbGameGenre.igdb_game_id == 20)
    ).all()
    assert genre_ids == [300]
    platform_ids = db_session.scalars(
        select(IgdbGamePlatform.igdb_platform_id).where(
            IgdbGamePlatform.igdb_game_id == 21
        )
    ).all()
    assert platform_ids == [6]

    external = db_session.get(IgdbExternalGame, 2001)
    assert external is not None
    assert external.year == 2024


def test_update_batch_issues_constant_query_count(
    db_session: Session,
    mocker: MockerFixture,
):
    """Batch path must not grow queries linearly with batch size."""
    from sqlalchemy import event

    for game_id in range(30, 40):
        _create_game(db_session, game_id)
    db_session.flush()
    queries: list[str] = []
    engine = db_session.get_bind()

    def _count(conn, cursor, statement, parameters, context, executemany) -> None:
        """Record each statement executed during the batch."""
        queries.append(statement)

    event.listen(engine, "before_cursor_execute", _count)
    try:
        IgdbGameUpdater(db_session).update_batch(
            list(range(30, 40)),
            covers={game_id: f"cover{game_id}" for game_id in range(30, 40)},
            genres={
                game_id: [GenreResponse(id=400, name="Shared Genre")]
                for game_id in range(30, 40)
            },
            platforms={game_id: [6] for game_id in range(30, 40)},
            time_to_beats={game_id: 1000 + game_id for game_id in range(30, 40)},
            now=datetime.now(tz=timezone.utc),
        )
    finally:
        event.remove(engine, "before_cursor_execute", _count)

    # 10 games with genres/platforms/TTBs: ~10 set-based statements,
    # far below the old ~60+ per-game round-trips for the same batch.
    assert len(queries) < 20


# --- run tests ---


def test_run_skips_when_lock_is_held(
    db_session: Session,
    mocker: MockerFixture,
):
    igdb_client = mocker.Mock()
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.IgdbClient.create",
        return_value=igdb_client,
    )
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.create_db_session",
        side_effect=lambda: _fake_db_session(db_session),
    )
    job = RefreshIgdbGamesJob()
    mocker.patch.object(job, "_acquire_lock", return_value=False)
    app_user = _create_app_user(db_session)

    job.run(app_user.app_user_id)

    igdb_client.get_covers_by_game_ids.assert_not_called()


def test_run_processes_stale_games_in_batches(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(
        db_session,
        1,
        last_refreshed_at=datetime.now(tz=timezone.utc) - timedelta(days=31),
    )
    _create_game(
        db_session,
        2,
        last_refreshed_at=datetime.now(tz=timezone.utc) - timedelta(days=40),
    )
    igdb_client = mocker.Mock()
    igdb_client.get_covers_by_game_ids.return_value = {}
    igdb_client.get_genres_by_game_ids.return_value = {}
    igdb_client.get_platforms_by_game_ids.return_value = {}
    igdb_client.get_game_time_to_beats.return_value = []
    igdb_client.get_external_games.return_value = []
    igdb_client.get_ratings_by_game_ids.return_value = {}
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.IgdbClient.create",
        return_value=igdb_client,
    )
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.create_db_session",
        side_effect=lambda: _fake_db_session(db_session),
    )
    mocker.patch("app.features.admin.refresh_igdb_games_job.time.sleep")
    job = RefreshIgdbGamesJob()
    mocker.patch.object(job, "_acquire_lock", return_value=True)
    app_user = _create_app_user(db_session)

    job.run(app_user.app_user_id)

    igdb_client.get_covers_by_game_ids.assert_called_once()
    called_ids = igdb_client.get_covers_by_game_ids.call_args[0][0]
    assert set(called_ids) == {1, 2}


def test_run_releases_lock_on_completion(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(
        db_session,
        1,
        last_refreshed_at=datetime.now(tz=timezone.utc) - timedelta(days=31),
    )
    igdb_client = mocker.Mock()
    igdb_client.get_covers_by_game_ids.return_value = {}
    igdb_client.get_genres_by_game_ids.return_value = {}
    igdb_client.get_platforms_by_game_ids.return_value = {}
    igdb_client.get_game_time_to_beats.return_value = []
    igdb_client.get_external_games.return_value = []
    igdb_client.get_ratings_by_game_ids.return_value = {}
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.IgdbClient.create",
        return_value=igdb_client,
    )
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.create_db_session",
        side_effect=lambda: _fake_db_session(db_session),
    )
    mocker.patch("app.features.admin.refresh_igdb_games_job.time.sleep")
    job = RefreshIgdbGamesJob()
    mocker.patch.object(job, "_acquire_lock", return_value=True)
    app_user = _create_app_user(db_session)

    job.run(app_user.app_user_id)

    lock = db_session.scalars(
        select(IgdbRefreshLock).where(IgdbRefreshLock.lock_id == LOCK_ID)
    ).one_or_none()
    assert lock is None


def test_run_releases_lock_on_error(
    db_session: Session,
    mocker: MockerFixture,
):
    igdb_client = mocker.Mock()
    igdb_client.get_covers_by_game_ids.side_effect = RuntimeError("IGDB down")
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.IgdbClient.create",
        return_value=igdb_client,
    )
    stale_time = datetime.now(tz=timezone.utc) - timedelta(days=31)
    _create_game(db_session, 1, last_refreshed_at=stale_time)
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.create_db_session",
        side_effect=lambda: _fake_db_session(db_session),
    )
    mocker.patch("app.features.admin.refresh_igdb_games_job.time.sleep")
    job = RefreshIgdbGamesJob()
    mocker.patch.object(job, "_acquire_lock", return_value=True)
    app_user = _create_app_user(db_session)

    with pytest.raises(RuntimeError, match="IGDB down"):
        job.run(app_user.app_user_id)

    lock = db_session.scalars(
        select(IgdbRefreshLock).where(IgdbRefreshLock.lock_id == LOCK_ID)
    ).one_or_none()
    assert lock is None
