from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/api/health/liveness")
def liveness():
    return {"message": "ready"}


@health_router.get("/api/health/readiness")
def readiness():
    return {"message": "ready"}
