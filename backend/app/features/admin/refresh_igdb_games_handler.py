from fastapi import BackgroundTasks

from app.database.engine import DbSession
from app.features.api_model import ApiResponseModel
from app.features.auth.get_current_user import RequiredCurrentUser
from app.features.admin.refresh_igdb_games_job import RefreshIgdbGamesJob


class RefreshIgdbGamesResponse(ApiResponseModel):
    status: str


class RefreshIgdbGamesHandler:
    def __init__(self, db: DbSession, current_user: RequiredCurrentUser):
        self.db = db
        self.current_user = current_user

    def handle(self, background_tasks: BackgroundTasks) -> RefreshIgdbGamesResponse:
        """Start the IGDB game refresh background task.

        Args:
            background_tasks: Starlette background task queue.

        Returns:
            Acknowledgement that the refresh was started.
        """
        job = RefreshIgdbGamesJob()
        background_tasks.add_task(job.run, self.current_user.app_user_id)
        return RefreshIgdbGamesResponse(status="started")
