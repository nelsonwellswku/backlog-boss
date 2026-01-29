from fastapi import APIRouter, Depends

from app.features.user.create_my_backlog_handler import (
    CreateMyBacklogHandler,
    CreateMyBacklogResponse,
)
from app.features.user.get_me_handler import GetMeHandler, GetMeResponse
from app.features.user.get_my_backlog_handler import (
    GetMyBacklogHandler,
    GetMyBacklogResponse,
)

user_router = APIRouter(tags=["User"])


@user_router.get("/api/user/me")
def get_me(handler: GetMeHandler = Depends()) -> GetMeResponse:
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
