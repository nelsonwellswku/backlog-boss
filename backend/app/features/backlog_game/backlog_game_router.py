from fastapi import APIRouter, Depends

from app.features.backlog_game.add_backlog_game_handler import (
    AddBacklogGameHandler,
    AddBacklogGameRequest,
    AddBacklogGameResponse,
)
from app.features.backlog_game.update_backlog_game_handler import (
    UpdateBacklogGameHandler,
    UpdateBacklogGameRequest,
    UpdateBacklogGameResponse,
)

backlog_game_router = APIRouter(tags=["Backlog Game"])


@backlog_game_router.post("/api/backlog-game")
def add_game_to_backlog(
    add_backlog_game_request: AddBacklogGameRequest,
    handler: AddBacklogGameHandler = Depends(),
) -> AddBacklogGameResponse:
    return handler.handle(add_backlog_game_request)


@backlog_game_router.put("/api/backlog-game/{backlog_game_id}")
def update_game(
    backlog_game_id: int,
    update_backlog_game_request: UpdateBacklogGameRequest,
    handler: UpdateBacklogGameHandler = Depends(),
) -> UpdateBacklogGameResponse:
    return handler.handle(backlog_game_id, update_backlog_game_request)
