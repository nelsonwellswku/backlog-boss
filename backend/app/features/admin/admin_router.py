from fastapi import APIRouter, BackgroundTasks

from app.auth.dependencies import requires_authorization
from app.auth.permissions import Permission, Resource
from app.features.admin.refresh_igdb_games_handler import (
    RefreshIgdbGamesHandlerDep,
    RefreshIgdbGamesResponse,
)

admin_router = APIRouter(tags=["Admin"])


@admin_router.post(
    "/api/admin/refresh-igdb-games",
    status_code=202,
    dependencies=[requires_authorization(Permission.WRITE, Resource.IGDB_GAMES)],
)
def refresh_igdb_games(
    background_tasks: BackgroundTasks,
    handler: RefreshIgdbGamesHandlerDep,
) -> RefreshIgdbGamesResponse:
    return handler.handle(background_tasks)
