from logging import getLogger
from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.engine import DbSession
from app.database.models import IgdbGame, IgdbGamePlatform, IgdbPlatform
from app.infrastructure.igdb_client import IgdbClientDep

logger = getLogger(__name__)


class PlatformFetcher:
    def __init__(self, db: DbSession, igdb_client: IgdbClientDep):
        self.db = db
        self.igdb_client = igdb_client

    def fetch_and_persist(self, game_ids: list[int]) -> None:
        """Fetch platforms from IGDB for games that are missing them and persist.

        Args:
            game_ids: IGDB game IDs to check and potentially update.
        """
        stmt = select(IgdbGame.igdb_game_id).where(
            IgdbGame.igdb_game_id.in_(game_ids),
            ~select(IgdbGamePlatform.igdb_game_id)
            .where(IgdbGamePlatform.igdb_game_id == IgdbGame.igdb_game_id)
            .exists(),
        )
        missing_ids = list(self.db.scalars(stmt).all())

        if not missing_ids:
            logger.info("No games missing platforms among %d provided", len(game_ids))
            return

        platforms_by_game = self.igdb_client.get_platforms_by_game_ids(missing_ids)

        if not platforms_by_game:
            logger.info("IGDB returned no platforms for %d games", len(missing_ids))
            return

        stmt = (
            select(IgdbGame)
            .where(IgdbGame.igdb_game_id.in_(platforms_by_game.keys()))
            .options(selectinload(IgdbGame.platforms))
        )
        games = {g.igdb_game_id: g for g in self.db.scalars(stmt).all()}

        all_platform_ids = {
            pid for pid_list in platforms_by_game.values() for pid in pid_list
        }
        stmt = select(IgdbPlatform).where(
            IgdbPlatform.igdb_platform_id.in_(all_platform_ids)
        )
        existing_platforms = {
            p.igdb_platform_id: p for p in self.db.scalars(stmt).all()
        }

        for igdb_game_id, pid_list in platforms_by_game.items():
            game = games.get(igdb_game_id)
            if not game:
                continue

            for pid in pid_list:
                platform = existing_platforms.get(pid)
                if not platform:
                    platform = IgdbPlatform(igdb_platform_id=pid)
                    self.db.add(platform)
                    existing_platforms[pid] = platform
                game.platforms.append(platform)

        logger.info("Updated platforms for %d games", len(platforms_by_game))


PlatformFetcherDep: TypeAlias = Annotated[PlatformFetcher, Depends(PlatformFetcher)]
