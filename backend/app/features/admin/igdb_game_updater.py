import logging
from datetime import datetime

from sqlalchemy import delete, select

from app.database.engine import DbSession
from app.database.models import (
    IgdbExternalGame,
    IgdbGame,
    IgdbGameGenre,
    IgdbGamePlatform,
    IgdbGameTimeToBeat,
    IgdbGenre,
    IgdbPlatform,
)
from app.infrastructure.igdb_client import ExternalGameResponse, GenreResponse

logger = logging.getLogger(__name__)


class IgdbGameUpdater:
    """Persist refreshed IGDB data for games."""

    def __init__(self, db: DbSession):
        self.db = db

    def update_batch(
        self,
        game_ids: list[int],
        covers: dict[int, str],
        genres: dict[int, list[GenreResponse]],
        platforms: dict[int, list[int]],
        time_to_beats: dict[int, int | None],
        now: datetime,
        externals: dict[int, list[ExternalGameResponse]] | None = None,
        ratings: dict[int, float] | None = None,
    ) -> None:
        """Update a batch of games and their related data with set-based queries.

        Args:
            game_ids: IGDB ids in this batch.
            covers: Mapping of game id to cover image id.
            genres: Mapping of game id to genre data.
            platforms: Mapping of game id to platform ids.
            time_to_beats: Mapping of game id to normal time-to-beat value.
            now: Timestamp to stamp as last_refreshed_at.
            externals: Mapping of game id to external game data. Only existing
                rows are updated; missing rows are never inserted. A None year
                preserves the stored value.
            ratings: Mapping of game id to total rating. Missing values preserve
                the stored rating. Names are intentionally never updated.

        Games missing from every IGDB response are skipped entirely so
        last_refreshed_at stays stale and they retry on the next run.
        Missing genre/platform entries preserve existing associations.
        Does not commit; the caller owns the transaction.
        """
        db = self.db

        def _has_data(game_id: int) -> bool:
            """Return True when any IGDB payload covers the game."""
            return (
                game_id in covers
                or game_id in genres
                or game_id in platforms
                or game_id in time_to_beats
                or (externals is not None and game_id in externals)
                or (ratings is not None and game_id in ratings)
            )

        active_ids = [game_id for game_id in game_ids if _has_data(game_id)]
        if not active_ids:
            return

        # Load games once.
        games = {
            game.igdb_game_id: game
            for game in db.scalars(
                select(IgdbGame).where(IgdbGame.igdb_game_id.in_(active_ids))
            ).all()
        }
        if not games:
            return

        # Update core game fields in memory (no per-game queries).
        for game_id, game in games.items():
            if game_id in covers:
                game.cover_image_id = covers[game_id]
            if ratings and game_id in ratings:
                game.total_rating = ratings[game_id]
            game.last_refreshed_at = now

        # Load time-to-beat rows once. NOTE: IgdbGame.time_to_beat uses
        # lazy="raise", so it must not be accessed here. Query rows directly.
        ttb_ids = [game_id for game_id in games if game_id in time_to_beats]
        if ttb_ids:
            existing_ttbs = {
                ttb.igdb_game_id: ttb
                for ttb in db.scalars(
                    select(IgdbGameTimeToBeat).where(
                        IgdbGameTimeToBeat.igdb_game_id.in_(ttb_ids)
                    )
                ).all()
            }
            for game_id in ttb_ids:
                ttb_value = time_to_beats[game_id]
                existing = existing_ttbs.get(game_id)
                if existing is not None:
                    existing.normally = ttb_value
                else:
                    db.add(
                        IgdbGameTimeToBeat(
                            igdb_game_time_to_beat_id=game_id,
                            normally=ttb_value,
                            igdb_game_id=game_id,
                        )
                    )

        # Replace genres with one load, one bulk delete, and bulk inserts.
        genre_game_ids = [game_id for game_id in games if game_id in genres]
        if genre_game_ids:
            needed_genre_ids = {
                genre_data.id
                for game_id in genre_game_ids
                for genre_data in genres[game_id]
            }
            if needed_genre_ids:
                existing_genre_ids = set(
                    db.scalars(
                        select(IgdbGenre.igdb_genre_id).where(
                            IgdbGenre.igdb_genre_id.in_(needed_genre_ids)
                        )
                    ).all()
                )
                genre_names = {}
                for game_id in genre_game_ids:
                    for genre_data in genres[game_id]:
                        genre_names.setdefault(genre_data.id, genre_data.name)
                missing_genres = [
                    IgdbGenre(igdb_genre_id=genre_id, name=genre_names[genre_id])
                    for genre_id in needed_genre_ids
                    if genre_id not in existing_genre_ids
                ]
                if missing_genres:
                    db.add_all(missing_genres)
                    db.flush()
                db.execute(
                    delete(IgdbGameGenre).where(
                        IgdbGameGenre.igdb_game_id.in_(genre_game_ids)
                    )
                )
                db.add_all(
                    [
                        IgdbGameGenre(igdb_game_id=game_id, igdb_genre_id=genre_data.id)
                        for game_id in genre_game_ids
                        for genre_data in genres[game_id]
                    ]
                )

        # Replace platforms with one load, one bulk delete, and bulk inserts.
        platform_game_ids = [game_id for game_id in games if game_id in platforms]
        if platform_game_ids:
            needed_platform_ids = {
                platform_id
                for game_id in platform_game_ids
                for platform_id in platforms[game_id]
            }
            known_platform_ids: set[int] = set()
            if needed_platform_ids:
                known_platform_ids = set(
                    db.scalars(
                        select(IgdbPlatform.igdb_platform_id).where(
                            IgdbPlatform.igdb_platform_id.in_(needed_platform_ids)
                        )
                    ).all()
                )
            db.execute(
                delete(IgdbGamePlatform).where(
                    IgdbGamePlatform.igdb_game_id.in_(platform_game_ids)
                )
            )
            associations = []
            for game_id in platform_game_ids:
                for platform_id in platforms[game_id]:
                    if platform_id not in known_platform_ids:
                        logger.warning(
                            "Skipping unknown IgdbPlatform %s for game %s",
                            platform_id,
                            game_id,
                        )
                        continue
                    associations.append(
                        IgdbGamePlatform(
                            igdb_game_id=game_id, igdb_platform_id=platform_id
                        )
                    )
            if associations:
                db.add_all(associations)

        # Update external game years (update-only, never insert).
        if externals:
            external_game_ids = [game_id for game_id in games if game_id in externals]
            if external_game_ids:
                existing_externals = {
                    external.igdb_external_game_id: external
                    for external in db.scalars(
                        select(IgdbExternalGame).where(
                            IgdbExternalGame.igdb_game_id.in_(external_game_ids)
                        )
                    ).all()
                }
                for game_id in external_game_ids:
                    for external_data in externals[game_id]:
                        if external_data.year is None:
                            continue
                        existing = existing_externals.get(external_data.id)
                        if existing is not None:
                            existing.year = external_data.year

        db.flush()
