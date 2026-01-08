from fastapi import APIRouter
from pydantic import BaseModel

health_router = APIRouter()

class HealthResponse(BaseModel):
    message: str

@health_router.get("/api/health/liveness")
def liveness() -> HealthResponse:
    return HealthResponse(message="ready")


@health_router.get("/api/health/readiness")
def readiness() -> HealthResponse:
    return HealthResponse(message="ready")
