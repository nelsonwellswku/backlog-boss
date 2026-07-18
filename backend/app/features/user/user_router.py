from fastapi import APIRouter, BackgroundTasks, Depends

from app.features.user.create_my_backlog_handler import (
    CreateMyBacklogHandler,
    CreateMyBacklogResponse,
)
from app.features.user.fetch_missing_covers_task import (
    fetch_missing_covers_task,
)
from app.features.user.fetch_missing_genres_task import (
    fetch_missing_genres_task,
)
from app.features.user.get_me_handler import GetMeHandler, GetMeResponse
from app.features.user.get_my_backlog_handler import (
    GetMyBacklogHandler,
    GetMyBacklogResponse,
)
from app.features.user.refresh_my_backlog_handler import (
    RefreshMyBacklogHandler,
    RefreshMyBacklogResponse,
)

user_router = APIRouter(tags=["User"])


@user_router.get("/api/user/me")
def get_me(handler: GetMeHandler = Depends()) -> GetMeResponse | None:
    return handler.handle()


@user_router.post("/api/user/create-my-backlog")
def create_my_backlog(
    handler: CreateMyBacklogHandler = Depends(),
) -> CreateMyBacklogResponse:
    return handler.handle()


@user_router.get("/api/user/get-my-backlog")
def get_my_backlog(
    handler: GetMyBacklogHandler = Depends(),
) -> GetMyBacklogResponse:
    return handler.handle()


@user_router.post("/api/user/refresh-my-backlog")
def refresh_my_backlog(
    bg_tasks: BackgroundTasks,
    handler: RefreshMyBacklogHandler = Depends(),
) -> RefreshMyBacklogResponse:
    result = handler.handle()
    bg_tasks.add_task(fetch_missing_covers_task, result.backlog_id)
    bg_tasks.add_task(fetch_missing_genres_task, result.backlog_id)
    return result
