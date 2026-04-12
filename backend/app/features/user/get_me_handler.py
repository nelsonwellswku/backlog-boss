from app.features.api_model import ApiResponseModel
from app.features.auth.get_current_user import CurrentUser


class GetMeResponse(ApiResponseModel):
    app_user_id: int
    steam_id: str
    persona_name: str


class GetMeHandler:
    def __init__(self, current_user: CurrentUser):
        self.current_user = current_user

    def handle(self):
        return GetMeResponse(
            app_user_id=self.current_user.app_user_id,
            steam_id=self.current_user.steam_id,
            persona_name=self.current_user.persona_name,
        )
