from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import joinedload

from app.database.engine import DbSession
from app.database.models import IgdbExternalGame, IgdbGame
from app.features.api_model import ApiResponseModel
from app.features.game.persist_igdb_games import persist_igdb_games
from app.infrastructure.igdb_client import IgdbClientDep


class GameSearchRow(ApiResponseModel):
    game_id: int
    title: str
    total_rating: float | None
    time_to_beat: int | None


class SearchGamesResponse(ApiResponseModel):
    games: list[GameSearchRow]


class SearchGamesHandler:
    def __init__(self, db: DbSession, igdb_client: IgdbClientDep):
        self.db = db
        self.igdb_client = igdb_client

    def handle(self, query: str) -> SearchGamesResponse:
        normalized_query = query.strip()
        if not normalized_query:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "Search query must not be blank.",
            )

        database_games = self._search_database(normalized_query)
        if database_games:
            return SearchGamesResponse(
                games=[self._build_game_search_row(game) for game in database_games]
            )

        igdb_games = self.igdb_client.search_games_by_name(normalized_query)
        persist_igdb_games(self.db, igdb_games)
        if igdb_games:
            self.db.commit()
        if not igdb_games:
            return SearchGamesResponse(games=[])

        persisted_games = self._load_games_by_ids([game.id for game in igdb_games])
        return SearchGamesResponse(
            games=[self._build_game_search_row(game) for game in persisted_games]
        )

    def _search_database(self, query: str) -> list[IgdbGame]:
        normalized_query = query.lower()
        ordering = case(
            (func.lower(IgdbGame.name) == normalized_query, 0),
            (func.lower(IgdbGame.name).like(f"{normalized_query}%"), 1),
            else_=2,
        )
        matching_game_ids = self.db.scalars(
            select(IgdbGame.igdb_game_id)
            .join(IgdbExternalGame)
            .where(IgdbExternalGame.igdb_external_game_source_id == 1)
            .where(func.lower(IgdbGame.name).contains(normalized_query))
            .group_by(IgdbGame.igdb_game_id, IgdbGame.name)
            .order_by(ordering, IgdbGame.name)
            .limit(50)
        ).all()
        return self._load_games_by_ids(matching_game_ids)

    def _load_games_by_ids(self, game_ids: Sequence[int]) -> list[IgdbGame]:
        if not game_ids:
            return []

        stmt = (
            select(IgdbGame)
            .join(IgdbExternalGame)
            .options(joinedload(IgdbGame.time_to_beat))
            .where(IgdbExternalGame.igdb_external_game_source_id == 1)
            .where(IgdbGame.igdb_game_id.in_(game_ids))
            .distinct()
        )
        games = self.db.scalars(stmt).unique().all()
        games_by_id = {game.igdb_game_id: game for game in games}
        return [games_by_id[game_id] for game_id in game_ids if game_id in games_by_id]

    def _build_game_search_row(self, game: IgdbGame) -> GameSearchRow:
        return GameSearchRow(
            game_id=game.igdb_game_id,
            title=game.name,
            total_rating=game.total_rating,
            time_to_beat=game.time_to_beat.normally if game.time_to_beat else None,
        )
