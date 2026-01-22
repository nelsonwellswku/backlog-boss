from fastapi import APIRouter, Depends

from app.features.user.create_my_backlog_command import (
    CreateMyBacklogCommand,
    CreateMyBacklogResponse,
)
from app.features.user.get_me_query import GetMeQuery, GetMeResponse
from app.features.user.get_my_backlog_query import (
    GetMyBacklogQuery,
    GetMyBacklogResponse,
)

user_router = APIRouter(tags=["User"])


@user_router.get("/api/user/me")
def get_me(query: GetMeQuery = Depends()) -> GetMeResponse:
    return query.execute()


@user_router.post("/api/user/create-my-backlog")
def create_my_backlog(
    command: CreateMyBacklogCommand = Depends(),
) -> CreateMyBacklogResponse:
    return command.execute()


@user_router.get("/api/user/get-my-backlog")
def get_my_backlog(
    query: GetMyBacklogQuery = Depends(),
) -> GetMyBacklogResponse:
    return query.execute()
