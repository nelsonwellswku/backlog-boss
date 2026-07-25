from logging import getLogger
from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.engine import DbSession
from app.database.models import IgdbGame, IgdbGameGenre, IgdbGenre
from app.infrastructure.igdb_client import IgdbClientDep

logger = getLogger(__name__)


class GenreFetcher:
    def __init__(self, db: DbSession, igdb_client: IgdbClientDep):
        self.db = db
        self.igdb_client = igdb_client

    def fetch_and_persist(self, game_ids: list[int]) -> None:
        """Fetch genres from IGDB for games that are missing them and persist.

        Args:
            game_ids: IGDB game IDs to check and potentially update.
        """
        stmt = select(IgdbGame.igdb_game_id).where(
            IgdbGame.igdb_game_id.in_(game_ids),
            ~select(IgdbGameGenre.igdb_game_id)
            .where(IgdbGameGenre.igdb_game_id == IgdbGame.igdb_game_id)
            .exists(),
        )
        missing_ids = list(self.db.scalars(stmt).all())

        if not missing_ids:
            logger.info("No games missing genres among %d provided", len(game_ids))
            return

        genres_by_game = self.igdb_client.get_genres_by_game_ids(missing_ids)

        if not genres_by_game:
            logger.info("IGDB returned no genres for %d games", len(missing_ids))
            return

        stmt = (
            select(IgdbGame)
            .where(IgdbGame.igdb_game_id.in_(genres_by_game.keys()))
            .options(selectinload(IgdbGame.genres))
        )
        games = {g.igdb_game_id: g for g in self.db.scalars(stmt).all()}

        all_genre_ids = {gr.id for genre_list in genres_by_game.values() for gr in genre_list}
        stmt = select(IgdbGenre).where(IgdbGenre.igdb_genre_id.in_(all_genre_ids))
        existing_genres = {g.igdb_genre_id: g for g in self.db.scalars(stmt).all()}

        updated = 0
        for igdb_game_id, genre_list in genres_by_game.items():
            game = games.get(igdb_game_id)
            if not game:
                continue

            for genre_response in genre_list:
                genre = existing_genres.get(genre_response.id)
                if not genre:
                    genre = IgdbGenre(
                        igdb_genre_id=genre_response.id,
                        name=genre_response.name,
                    )
                    self.db.add(genre)
                    existing_genres[genre_response.id] = genre
                game.genres.append(genre)
                updated += 1

        logger.info("Updated genres for %d games", updated)


GenreFetcherDep: TypeAlias = Annotated[GenreFetcher, Depends(GenreFetcher)]
