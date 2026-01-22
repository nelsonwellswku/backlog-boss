from pydantic import BaseModel, Field

from app.features.auth.get_current_user import CurrentUser


class GetMeResponse(BaseModel):
    app_user_id: int = Field(serialization_alias="appUserId")
    steam_id: str = Field(serialization_alias="steamId")
    persona_name: str = Field(serialization_alias="personaName")


class GetMeQuery:
    def __init__(self, current_user: CurrentUser):
        self.current_user = current_user

    def execute(self):
        return GetMeResponse(
            app_user_id=self.current_user.app_user_id,
            steam_id=self.current_user.steam_id,
            persona_name=self.current_user.persona_name,
        )
