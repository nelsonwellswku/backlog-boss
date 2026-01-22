from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.features.auth.get_current_user import CurrentUser
from app.features.user.create_my_backlog_command import (
    CreateMyBacklogCommand,
    CreateMyBacklogResponse,
)
from app.features.user.get_my_backlog_query import (
    GetMyBacklogQuery,
    GetMyBacklogResponse,
)

user_router = APIRouter()


class CurrentUserResponse(BaseModel):
    app_user_id: int = Field(serialization_alias="appUserId")
    steam_id: str = Field(serialization_alias="steamId")
    persona_name: str = Field(serialization_alias="personaName")


@user_router.get("/api/user/me")
def get_me(current_user: CurrentUser) -> CurrentUserResponse:
    return CurrentUserResponse(
        app_user_id=current_user.app_user_id,
        steam_id=current_user.steam_id,
        persona_name=current_user.persona_name,
    )


@user_router.post("/api/user/create-my-backlog")
def create_my_backlog(
    command: CreateMyBacklogCommand = Depends(CreateMyBacklogCommand),
) -> CreateMyBacklogResponse:
    return command.execute()


@user_router.get("/api/user/get-my-backlog")
def get_my_backlog(
    query: GetMyBacklogQuery = Depends(GetMyBacklogQuery),
) -> GetMyBacklogResponse:
    return query.execute()
