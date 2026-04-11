from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database.engine import DbSession
from app.database.models import Backlog, BacklogGame
from app.features.api_model import ApiRequestModel, ApiResponseModel
from app.features.auth.get_current_user import CurrentUser


class UpdateBacklogGameRequest(ApiRequestModel):
    completed_on: datetime | None
    removed_on: datetime | None


class UpdateBacklogGameResponse(ApiResponseModel):
    backlog_game_id: int


class UpdateBacklogHandler:
    def __init__(self, db: DbSession, current_user: CurrentUser):
        self.db = db
        self.current_user = current_user

    def handle(self, backlog_game_id: int, request: UpdateBacklogGameRequest):
        stmt = (
            select(BacklogGame)
            .where(BacklogGame.backlog_game_id == backlog_game_id)
            .options(joinedload(BacklogGame.backlog))
        )
        backlog_game = self.db.scalars(stmt).one_or_none()

        if not backlog_game:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Backlog game not found.")

        if backlog_game.backlog.app_user_id != self.current_user.app_user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")

        backlog_game.completed_on = request.completed_on
        backlog_game.removed_on = request.removed_on

        self.db.commit()

        return UpdateBacklogGameResponse(backlog_game_id=backlog_game_id)
