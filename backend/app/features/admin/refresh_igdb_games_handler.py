from typing import Annotated, TypeAlias

from fastapi import BackgroundTasks, Depends

from app.features.admin.refresh_igdb_games_job import RefreshIgdbGamesJob
from app.features.api_model import ApiResponseModel
from app.features.auth.get_current_user import RequiredCurrentUser


class RefreshIgdbGamesResponse(ApiResponseModel):
    status: str


class RefreshIgdbGamesHandler:
    def __init__(self, current_user: RequiredCurrentUser):
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


RefreshIgdbGamesHandlerDep: TypeAlias = Annotated[
    RefreshIgdbGamesHandler, Depends(RefreshIgdbGamesHandler)
]
