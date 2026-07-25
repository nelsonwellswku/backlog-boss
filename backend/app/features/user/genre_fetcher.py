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

    def fetch(self, game_ids: list[int]) -> None:
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

        updated = 0
        for igdb_game_id, genre_list in genres_by_game.items():
            stmt = (
                select(IgdbGame)
                .where(IgdbGame.igdb_game_id == igdb_game_id)
                .options(selectinload(IgdbGame.genres))
            )
            game = self.db.scalars(stmt).one_or_none()
            if not game:
                continue

            for genre_response in genre_list:
                genre = self.db.get(IgdbGenre, genre_response.id)
                if not genre:
                    genre = IgdbGenre(
                        igdb_genre_id=genre_response.id,
                        name=genre_response.name,
                    )
                    self.db.add(genre)
                game.genres.append(genre)
                updated += 1

        logger.info("Updated genres for %d games", updated)


GenreFetcherDep: TypeAlias = Annotated[GenreFetcher, Depends(GenreFetcher)]
