from fastapi import HTTPException, status
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import Backlog, BacklogGame, IgdbGame
from app.features.api_model import ApiRequestModel, ApiResponseModel
from app.features.auth.get_current_user import CurrentUser


class AddBacklogGameRequest(ApiRequestModel):
    game_id: int


class AddBacklogGameResponse(ApiResponseModel):
    backlog_game_id: int


class AddBacklogGameHandler:
    def __init__(self, db: DbSession, current_user: CurrentUser):
        self.db = db
        self.current_user = current_user

    def handle(self, request: AddBacklogGameRequest) -> AddBacklogGameResponse:
        stmt = select(Backlog).where(
            Backlog.app_user_id == self.current_user.app_user_id
        )
        backlog = self.db.scalars(stmt).one_or_none()
        if not backlog:
            backlog = Backlog(app_user_id=self.current_user.app_user_id)
            self.db.add(backlog)
            self.db.flush()

        game = self.db.get(IgdbGame, request.game_id)
        if not game:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found.")

        active_stmt = select(BacklogGame).where(
            BacklogGame.backlog_id == backlog.backlog_id,
            BacklogGame.igdb_game_id == request.game_id,
            BacklogGame.removed_on.is_(None),
        )
        active = self.db.scalars(active_stmt).one_or_none()
        if active:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Game is already in your backlog."
            )

        removed_stmt = (
            select(BacklogGame)
            .where(
                BacklogGame.backlog_id == backlog.backlog_id,
                BacklogGame.igdb_game_id == request.game_id,
                BacklogGame.removed_on.isnot(None),
            )
            .order_by(BacklogGame.removed_on.desc())
            .limit(1)
        )
        removed = self.db.scalars(removed_stmt).first()
        if removed:
            removed.removed_on = None
            self.db.commit()
            return AddBacklogGameResponse(backlog_game_id=removed.backlog_game_id)

        backlog_game = BacklogGame(
            backlog_id=backlog.backlog_id,
            igdb_game_id=request.game_id,
        )
        self.db.add(backlog_game)
        self.db.commit()

        return AddBacklogGameResponse(backlog_game_id=backlog_game.backlog_game_id)
