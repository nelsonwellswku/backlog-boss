from fastapi import APIRouter, BackgroundTasks, Depends

from app.auth.dependencies import requires_authorization
from app.auth.permissions import Permission, Resource
from app.features.admin.refresh_igdb_games_handler import (
    RefreshIgdbGamesHandler,
    RefreshIgdbGamesResponse,
)

admin_router = APIRouter(tags=["Admin"])


@admin_router.post(
    "/api/admin/refresh-igdb-games",
    dependencies=[requires_authorization(Permission.WRITE, Resource.IGDB_GAMES)],
)
def refresh_igdb_games(
    background_tasks: BackgroundTasks,
    handler: RefreshIgdbGamesHandler = Depends(),
) -> RefreshIgdbGamesResponse:
    return handler.handle(background_tasks)
