from logging import getLogger

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database.engine import DbSession
from app.database.models import Backlog, BacklogGame, IgdbGame
from app.features.auth.get_current_user import CurrentUser

logger = getLogger(__name__)


class GetMyBacklogResponse(BaseModel):
    backlog_id: int = Field(serialization_alias="backlogId")
    games: list["BacklogGameRow"]


class BacklogGameRow(BaseModel):
    game_id: int = Field(serialization_alias="gameId")
    title: str
    total_rating: float | None = Field(serialization_alias="totalRating")
    time_to_beat: int | None = Field(serialization_alias="timeToBeat")


class GetMyBacklogHandler:
    def __init__(self, db: DbSession, current_user: CurrentUser):
        self.db = db
        self.current_user = current_user

    def handle(self):
        stmt = (
            select(Backlog)
            .options(
                joinedload(Backlog.backlog_games)
                .joinedload(BacklogGame.igdb_game)
                .joinedload(IgdbGame.time_to_beat)
            )
            .where(Backlog.app_user_id == self.current_user.app_user_id)
        )

        backlog = self.db.scalars(stmt).unique().one_or_none()
        if not backlog:
            raise HTTPException(404, "Backlog not found.")

        backlog_game_rows = [
            BacklogGameRow(
                game_id=g.igdb_game_id,
                title=g.igdb_game.name,
                total_rating=g.igdb_game.total_rating,
                time_to_beat=g.igdb_game.time_to_beat.normally
                if g.igdb_game.time_to_beat
                else None,
            )
            for g in backlog.backlog_games
        ]

        return GetMyBacklogResponse(
            backlog_id=backlog.backlog_id, games=backlog_game_rows
        )
