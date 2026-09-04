import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update

from app.database.engine import create_db_session
from app.database.models import (
    IgdbGame,
    IgdbGameGenre,
    IgdbGamePlatform,
    IgdbGameTimeToBeat,
    IgdbGenre,
    IgdbPlatform,
    IgdbRefreshLock,
)
from app.infrastructure.igdb_client import IgdbClient

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
BATCH_DELAY_SECONDS = 1
STALENESS_THRESHOLD_DAYS = 30
LOCK_STALE_THRESHOLD_MINUTES = 5
LOCK_ID = "igdb_refresh"


class RefreshIgdbGamesJob:
    """Background job that refreshes stale IGDB game data."""

    def run(self, app_user_id: int) -> None:
        """Execute the refresh job.

        Args:
            app_user_id: Id of the admin user who triggered the refresh.
                Recorded on the lock row to satisfy the FK to AppUser.
        """
        igdb_client = IgdbClient.create()

        with create_db_session() as db:
            try:
                if not self._acquire_lock(db, app_user_id):
                    logger.info("Refresh already running, skipping")
                    return

                game_ids = self._get_stale_game_ids(db)
                if not game_ids:
                    logger.info("No stale games to refresh")
                    self._release_lock(db)
                    return

                logger.info("Starting refresh for %d games", len(game_ids))

                for i in range(0, len(game_ids), BATCH_SIZE):
                    batch_ids = game_ids[i : i + BATCH_SIZE]
                    self._process_batch(db, igdb_client, batch_ids)

                self._release_lock(db)
                logger.info("Refresh completed")
            except Exception:
                db.rollback()
                try:
                    self._release_lock(db)
                except Exception:
                    db.rollback()
                    raise
                raise

    def _acquire_lock(self, db, app_user_id: int) -> bool:
        """Try to acquire the refresh lock.

        Args:
            db: Active SQLAlchemy session.
            app_user_id: Id of the user acquiring the lock.

        Returns True if lock was acquired, False if already running.
        """
        now = datetime.now(tz=timezone.utc)
        stmt = select(IgdbRefreshLock).where(IgdbRefreshLock.lock_id == LOCK_ID)
        existing_lock = db.scalars(stmt).one_or_none()

        if existing_lock is not None:
            time_since_update = now - existing_lock.last_updated_on
            if time_since_update < timedelta(minutes=LOCK_STALE_THRESHOLD_MINUTES):
                return False

            # Stale lock, take over
            db.execute(
                update(IgdbRefreshLock)
                .where(IgdbRefreshLock.lock_id == LOCK_ID)
                .values(
                    last_updated_on=now,
                    started_on=now,
                    app_user_id=app_user_id,
                )
            )
        else:
            lock = IgdbRefreshLock(
                lock_id=LOCK_ID,
                started_on=now,
                last_updated_on=now,
                app_user_id=app_user_id,
            )
            db.add(lock)

        db.commit()
        return True

    def _release_lock(self, db) -> None:
        """Release the refresh lock.

        Args:
            db: Active SQLAlchemy session.
        """
        db.execute(delete(IgdbRefreshLock).where(IgdbRefreshLock.lock_id == LOCK_ID))
        db.commit()

    def _get_stale_game_ids(self, db) -> list[int]:
        """Get game IDs that need refreshing."""
        threshold = datetime.now(tz=timezone.utc) - timedelta(
            days=STALENESS_THRESHOLD_DAYS
        )
        stmt = select(IgdbGame.igdb_game_id).where(
            (IgdbGame.last_refreshed_at == None)  # noqa: E711
            | (IgdbGame.last_refreshed_at < threshold)
        )
        return list(db.scalars(stmt).all())

    def _process_batch(self, db, igdb_client: IgdbClient, game_ids: list[int]) -> None:
        """Process a batch of games."""
        logger.info("Processing batch of %d games", len(game_ids))

        # Fetch data from IGDB
        covers = igdb_client.get_covers_by_game_ids(game_ids)
        genres = igdb_client.get_genres_by_game_ids(game_ids)
        platforms = igdb_client.get_platforms_by_game_ids(game_ids)
        time_to_beats_list = igdb_client.get_game_time_to_beats(game_ids)

        # Convert time_to_beats list to dict keyed by game_id
        time_to_beats = {}
        for ttb in time_to_beats_list:
            time_to_beats[ttb.game_id] = ttb.normally

        now = datetime.now(tz=timezone.utc)

        # Begin transaction
        try:
            # Update games
            for game_id in game_ids:
                self._update_game(
                    db, game_id, covers, genres, platforms, time_to_beats, now
                )

            # Update lock timestamp
            db.execute(
                update(IgdbRefreshLock)
                .where(IgdbRefreshLock.lock_id == LOCK_ID)
                .values(last_updated_on=now)
            )

            db.commit()
        except Exception:
            db.rollback()
            raise

        time.sleep(BATCH_DELAY_SECONDS)

    def _update_game(
        self,
        db,
        game_id: int,
        covers: dict[int, str],
        genres: dict[int, list],
        platforms: dict[int, list[int]],
        time_to_beats: dict[int, int | None],
        now: datetime,
    ) -> None:
        """Update a single game and its related data.

        Args:
            db: Active SQLAlchemy session.
            game_id: IGDB id of the game to update.
            covers: Mapping of game id to cover image id.
            genres: Mapping of game id to genre data.
            platforms: Mapping of game id to platform ids.
            time_to_beats: Mapping of game id to normal time-to-beat value.
            now: Timestamp to stamp as last_refreshed_at.
        """
        # Update core game fields
        game = db.get(IgdbGame, game_id)
        if game is None:
            return

        if game_id in covers:
            game.cover_image_id = covers[game_id]
        game.last_refreshed_at = now

        # Update time to beat. NOTE: IgdbGame.time_to_beat uses lazy="raise",
        # so it must not be accessed here (db.get never eager-loads it).
        # Query the row directly instead.
        if game_id in time_to_beats:
            ttb_value = time_to_beats[game_id]
            ttb = db.scalars(
                select(IgdbGameTimeToBeat).where(
                    IgdbGameTimeToBeat.igdb_game_id == game_id
                )
            ).one_or_none()
            if ttb is not None:
                ttb.normally = ttb_value
            else:
                db.add(
                    IgdbGameTimeToBeat(
                        igdb_game_time_to_beat_id=game_id,
                        normally=ttb_value,
                        igdb_game_id=game_id,
                    )
                )

        # Replace genres
        if game_id in genres:
            db.execute(
                delete(IgdbGameGenre).where(IgdbGameGenre.igdb_game_id == game_id)
            )
            for genre_data in genres[game_id]:
                genre_id = genre_data.id
                # Ensure genre exists, flushing it first so the association
                # row below never precedes its parent row.
                if db.get(IgdbGenre, genre_id) is None:
                    db.add(IgdbGenre(igdb_genre_id=genre_id, name=genre_data.name))
                    db.flush()
                db.add(IgdbGameGenre(igdb_game_id=game_id, igdb_genre_id=genre_id))

        # Replace platforms
        if game_id in platforms:
            db.execute(
                delete(IgdbGamePlatform).where(IgdbGamePlatform.igdb_game_id == game_id)
            )
            for platform_id in platforms[game_id]:
                # Ensure platform exists, flushing it first so the
                # association row below never precedes its parent row.
                if db.get(IgdbPlatform, platform_id) is None:
                    db.add(
                        IgdbPlatform(
                            igdb_platform_id=platform_id, name=str(platform_id)
                        )
                    )
                    db.flush()
                db.add(
                    IgdbGamePlatform(igdb_game_id=game_id, igdb_platform_id=platform_id)
                )
