import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update

from app.database.engine import create_db_session
from app.database.models import (
    IgdbGame,
    IgdbRefreshLock,
)
from app.features.admin.igdb_game_updater import IgdbGameUpdater
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
        """Get game IDs that need refreshing.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Ids of games whose last refresh is older than the staleness threshold.
        """
        threshold = datetime.now(tz=timezone.utc) - timedelta(
            days=STALENESS_THRESHOLD_DAYS
        )
        stmt = select(IgdbGame.igdb_game_id).where(
            IgdbGame.last_refreshed_at < threshold
        )
        return list(db.scalars(stmt).all())

    def _process_batch(self, db, igdb_client: IgdbClient, game_ids: list[int]) -> None:
        """Fetch fresh IGDB data for a batch and persist it atomically.

        Args:
            db: Active SQLAlchemy session.
            igdb_client: Client used to fetch covers, genres, platforms,
                time-to-beats, external games, and ratings.
            game_ids: IGDB ids in this batch.
        """
        logger.info("Processing batch of %d games", len(game_ids))

        # Fetch data from IGDB
        covers = igdb_client.get_covers_by_game_ids(game_ids)
        genres = igdb_client.get_genres_by_game_ids(game_ids)
        platforms = igdb_client.get_platforms_by_game_ids(game_ids)
        time_to_beats_list = igdb_client.get_game_time_to_beats(game_ids)
        external_games_list = igdb_client.get_external_games(game_ids)
        ratings = igdb_client.get_ratings_by_game_ids(game_ids)

        # Convert time_to_beats list to dict keyed by game_id
        time_to_beats = {}
        for ttb in time_to_beats_list:
            time_to_beats[ttb.game_id] = ttb.normally

        # Group external games by game_id
        externals: dict[int, list] = {}
        for external_game in external_games_list:
            externals.setdefault(external_game.game, []).append(external_game)

        now = datetime.now(tz=timezone.utc)

        # Begin transaction
        try:
            # Update games with set-based queries (single batch call).
            updater = IgdbGameUpdater(db)
            updater.update_batch(
                game_ids,
                covers,
                genres,
                platforms,
                time_to_beats,
                now,
                externals,
                ratings,
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
