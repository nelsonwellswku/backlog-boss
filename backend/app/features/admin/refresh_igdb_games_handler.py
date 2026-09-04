from fastapi import BackgroundTasks

from app.database.engine import DbSession
from app.features.api_model import ApiResponseModel
from app.features.admin.refresh_igdb_games_job import RefreshIgdbGamesJob


class RefreshIgdbGamesResponse(ApiResponseModel):
    status: str


class RefreshIgdbGamesHandler:
    def __init__(self, db: DbSession):
        self.db = db

    def handle(self, background_tasks: BackgroundTasks) -> RefreshIgdbGamesResponse:
        """Start the IGDB game refresh background task."""
        job = RefreshIgdbGamesJob()
        background_tasks.add_task(job.run)
        return RefreshIgdbGamesResponse(status="started")
