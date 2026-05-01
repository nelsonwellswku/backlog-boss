from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.features.game.search_games_handler import (
    SearchGamesHandler,
    SearchGamesResponse,
)

game_router = APIRouter(tags=["Game"])


@game_router.get("/api/games/search")
def search_games(
    query: Annotated[str, Query(min_length=1, max_length=100)],
    handler: SearchGamesHandler = Depends(),
) -> SearchGamesResponse:
    return handler.handle(query)
