from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.engine import DbSession
from app.features.api_model import ApiResponseModel


class GetReadinessResponse(ApiResponseModel):
    message: str


class GetReadinessHandler:
    def __init__(self, db: DbSession):
        self.db = db

    def handle(self) -> GetReadinessResponse:
        try:
            self.db.execute(text("SELECT 1")).scalar_one()
        except SQLAlchemyError as exc:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Database is not ready.",
            ) from exc

        return GetReadinessResponse(message="Database is ready.")
