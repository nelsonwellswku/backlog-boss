from fastapi import APIRouter, Depends, Response

from app.features.game.create_my_backlog_command import CreateMyBacklogCommand

game_router = APIRouter()


@game_router.post("/api/game/create_my_backlog")
def create_my_backlog(
    command: CreateMyBacklogCommand = Depends(CreateMyBacklogCommand),
) -> Response:
    return command.execute()
