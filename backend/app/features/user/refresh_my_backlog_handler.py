from fastapi import HTTPException, status
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import (
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
)
from app.features.api_model import ApiResponseModel
from app.features.auth.get_current_user import CurrentUser
from app.features.game.persist_igdb_games import persist_igdb_games
from app.infrastructure.igdb_client import IgdbClientDep
from app.infrastructure.steam_client import SteamClientDep


class RefreshMyBacklogResponse(ApiResponseModel):
    backlog_id: int
    games_added_count: int


class RefreshMyBacklogHandler:
    def __init__(
        self,
        db: DbSession,
        steam: SteamClientDep,
        current_user: CurrentUser,
        igdb_client: IgdbClientDep,
    ):
        self.db = db
        self.steam = steam
        self.current_user = current_user
        self.igdb_client = igdb_client

    def handle(self) -> RefreshMyBacklogResponse:
        stmt = select(Backlog).where(
            Backlog.app_user_id == self.current_user.app_user_id
        )
        backlog = self.db.scalars(stmt).one_or_none()
        if not backlog:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Backlog not found. Create one first.",
            )

        owned_games = self.steam.get_owned_games(self.current_user.steam_id)
        owned_game_steam_ids = {game.steam_game_id for game in owned_games}

        stmt = select(IgdbExternalGame.uid).where(
            IgdbExternalGame.uid.in_(owned_game_steam_ids)
        )
        games_in_db = self.db.scalars(stmt).all()
        games_in_db_ids = set(games_in_db)

        steam_game_ids_to_insert = owned_game_steam_ids - games_in_db_ids

        if steam_game_ids_to_insert:
            igdb_games = self.igdb_client.get_games_by_steam_id(
                steam_game_ids_to_insert
            )
            persist_igdb_games(self.db, igdb_games)

        stmt = (
            select(IgdbGame)
            .join(IgdbExternalGame)
            .where(IgdbExternalGame.uid.in_(owned_game_steam_ids))
            .where(IgdbGame.time_to_beat != None)  # noqa: E711
            .where(IgdbGame.total_rating != None)  # noqa: E711
            .distinct()
        )
        qualified_games = self.db.scalars(stmt).all()
        qualified_igdb_game_ids = {g.igdb_game_id for g in qualified_games}

        stmt = select(BacklogGame.igdb_game_id).where(
            BacklogGame.backlog_id == backlog.backlog_id
        )
        existing_igdb_game_ids = set(self.db.scalars(stmt).all())

        to_add_igdb_game_ids = qualified_igdb_game_ids - existing_igdb_game_ids

        new_backlog_games = [
            BacklogGame(backlog_id=backlog.backlog_id, igdb_game_id=gid)
            for gid in to_add_igdb_game_ids
        ]
        self.db.add_all(new_backlog_games)
        self.db.commit()

        return RefreshMyBacklogResponse(
            backlog_id=backlog.backlog_id,
            games_added_count=len(new_backlog_games),
        )
