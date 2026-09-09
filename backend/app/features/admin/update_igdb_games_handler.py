import logging
from datetime import datetime
from typing import Annotated, TypeAlias

from fastapi import Depends
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
from app.infrastructure.igdb_client import ExternalGameResponse

logger = logging.getLogger(__name__)


class UpdateIgdbGamesHandler:
    """Persist refreshed IGDB data for games."""

    def __init__(self, db: DbSession):
        self.db = db

    def update_game(
        self,
        game_id: int,
        covers: dict[int, str],
        genres: dict[int, list],
        platforms: dict[int, list[int]],
        time_to_beats: dict[int, int | None],
        now: datetime,
        externals: dict[int, list[ExternalGameResponse]] | None = None,
        ratings: dict[int, float] | None = None,
    ) -> None:
        """Update a single game and its related data.

        Args:
            game_id: IGDB id of the game to update.
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
        """
        db = self.db
        # Update core game fields
        game = db.get(IgdbGame, game_id)
        if game is None:
            return

        has_data = (
            game_id in covers
            or game_id in genres
            or game_id in platforms
            or game_id in time_to_beats
            or (externals is not None and game_id in externals)
            or (ratings is not None and game_id in ratings)
        )
        if not has_data:
            return

        if game_id in covers:
            game.cover_image_id = covers[game_id]
        if ratings and game_id in ratings:
            game.total_rating = ratings[game_id]
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
                if db.get(IgdbPlatform, platform_id) is None:
                    logger.warning(
                        "Skipping unknown IgdbPlatform %s for game %s",
                        platform_id,
                        game_id,
                    )
                    continue
                db.add(
                    IgdbGamePlatform(igdb_game_id=game_id, igdb_platform_id=platform_id)
                )

        # Update external game years (update-only, never insert).
        if externals and game_id in externals:
            for external_data in externals[game_id]:
                if external_data.year is None:
                    continue
                existing = db.get(IgdbExternalGame, external_data.id)
                if existing is not None:
                    existing.year = external_data.year


UpdateIgdbGamesHandlerDep: TypeAlias = Annotated[
    UpdateIgdbGamesHandler, Depends(UpdateIgdbGamesHandler)
]
