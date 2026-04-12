from app.features.api_model import ApiResponseModel


class GetLivenessResponse(ApiResponseModel):
    message: str


class GetLivenessHandler:
    def handle(self) -> GetLivenessResponse:
        return GetLivenessResponse(message="Service is up.")
