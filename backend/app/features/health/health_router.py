from fastapi import APIRouter, Depends

from app.features.health.get_liveness_handler import (
    GetLivenessHandler,
    GetLivenessResponse,
)
from app.features.health.get_readiness_handler import (
    GetReadinessHandler,
    GetReadinessResponse,
)

health_router = APIRouter(tags=["Health"])


@health_router.get("/api/health/liveness")
def liveness(handler: GetLivenessHandler = Depends()) -> GetLivenessResponse:
    return handler.handle()


@health_router.get("/api/health/readiness")
def readiness(
    handler: GetReadinessHandler = Depends(),
) -> GetReadinessResponse:
    return handler.handle()
