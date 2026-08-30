from datetime import timedelta

from fastapi import APIRouter, Depends, Query

from app.features.user.create_my_backlog_handler import (
    CreateMyBacklogHandler,
    CreateMyBacklogResponse,
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
from app.infrastructure.rate_limiter import RateLimited, RateLimitRule

user_router = APIRouter(tags=["User"])

_REFRESH_MY_BACKLOG_LIMIT = RateLimitRule(max_requests=1, window=timedelta(minutes=1))


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
    status: str | None = Query(None),
    handler: GetMyBacklogHandler = Depends(),
) -> GetMyBacklogResponse:
    return handler.handle(status=status)


@user_router.post(
    "/api/user/refresh-my-backlog",
    dependencies=[
        Depends(RateLimited(scope="refresh-my-backlog", rule=_REFRESH_MY_BACKLOG_LIMIT))
    ],
)
def refresh_my_backlog(
    handler: RefreshMyBacklogHandler = Depends(),
) -> RefreshMyBacklogResponse:
    return handler.handle()
