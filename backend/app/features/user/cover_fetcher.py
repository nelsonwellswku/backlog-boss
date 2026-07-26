from logging import getLogger
from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import IgdbGame
from app.infrastructure.igdb_client import IgdbClientDep

logger = getLogger(__name__)


class CoverFetcher:
    def __init__(self, db: DbSession, igdb_client: IgdbClientDep):
        self.db = db
        self.igdb_client = igdb_client

    def fetch_and_persist(self, game_ids: list[int]) -> None:
        """Fetch covers from IGDB for games that are missing them and persist.

        Args:
            game_ids: IGDB game IDs to check and potentially update.
        """
        stmt = select(IgdbGame.igdb_game_id).where(
            IgdbGame.igdb_game_id.in_(game_ids),
            IgdbGame.cover_image_id.is_(None),
        )
        missing_ids = list(self.db.scalars(stmt).all())

        if not missing_ids:
            logger.info("No games missing covers among %d provided", len(game_ids))
            return

        covers = self.igdb_client.get_covers_by_game_ids(missing_ids)

        if not covers:
            logger.info("IGDB returned no covers for %d games", len(missing_ids))
            return

        stmt = select(IgdbGame).where(IgdbGame.igdb_game_id.in_(covers.keys()))
        games = {g.igdb_game_id: g for g in self.db.scalars(stmt).all()}

        updated = 0
        for igdb_game_id, image_id in covers.items():
            game = games.get(igdb_game_id)
            if game and game.cover_image_id is None:
                game.cover_image_id = image_id
                updated += 1

        logger.info("Updated covers for %d games", updated)


CoverFetcherDep: TypeAlias = Annotated[CoverFetcher, Depends(CoverFetcher)]
