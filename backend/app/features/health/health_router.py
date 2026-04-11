from fastapi import APIRouter

from app.features.api_model import ApiResponseModel

health_router = APIRouter(tags=["Health"])


class HealthResponse(ApiResponseModel):
    message: str


@health_router.get("/api/health/liveness")
def liveness() -> HealthResponse:
    return HealthResponse(message="ready")


@health_router.get("/api/health/readiness")
def readiness() -> HealthResponse:
    return HealthResponse(message="ready")
