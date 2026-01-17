from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.features.auth.get_current_user import CurrentUser

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
