from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.features.backlog_game.update_backlog_game_handler import (
    UpdateBacklogGameRequest,
    UpdateBacklogHandler,
)

backlog_game_router = APIRouter(tags=["Backlog Game"])


@backlog_game_router.put("/api/backlog-game/{backlog_game_id}")
def update_game(
    backlog_game_id: int,
    update_backlog_game_request: UpdateBacklogGameRequest,
    handler: UpdateBacklogHandler = Depends(),
):
    return handler.handle(backlog_game_id, update_backlog_game_request)
