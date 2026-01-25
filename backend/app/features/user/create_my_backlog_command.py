from pydantic import BaseModel, Field
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import (
    Backlog,
    IgdbExternalGame,
    IgdbGame,
    IgdbGameTimeToBeat,
)
from app.features.auth.get_current_user import CurrentUser
from app.infrastructure.igdb_client import IgdbClientDep
from app.infrastructure.steam_client import SteamClientDep


class CreateMyBacklogResponse(BaseModel):
    backlog_id: int = Field(..., serialization_alias="backlogId")


class CreateMyBacklogCommand:
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

    # 1. fetches users owned games from steam
    # 2. fetches all of the games' details from igdb
    # 3. adds them to the game table in the database
    # 4. creates the user's backlog
    # 5. adds their owned games to the backlog
    def execute(self) -> CreateMyBacklogResponse:
        # if the user already has a backlog, return early
        # adding / removing items from the backlog can happen elsewhere
        stmt = select(Backlog).where(
            Backlog.app_user_id == self.current_user.app_user_id
        )
        backlog = self.db.scalars(stmt).one_or_none()
        if backlog:
            return CreateMyBacklogResponse(backlog_id=backlog.backlog_id)

        backlog = Backlog(app_user_id=self.current_user.app_user_id)

        # find the games the user owns but are not already in the database
        owned_games = self.steam.get_owned_games(self.current_user.steam_id)
        owned_game_steam_ids = set([game.steam_game_id for game in owned_games])

        # query for games already in the database with these steam_ids
        stmt = select(IgdbExternalGame.uid).where(
            IgdbExternalGame.uid.in_(owned_game_steam_ids)
        )
        games_in_db = self.db.scalars(stmt).all()
        games_in_db_ids = set(games_in_db)

        steam_game_ids_to_insert = owned_game_steam_ids - games_in_db_ids

        # fetch the games to insert from igdb and save them to the database
        igdb_games = self.igdb_client.get_games(steam_game_ids_to_insert)

        games_to_add: list[IgdbGame] = []
        for game in igdb_games:
            igdb_game = IgdbGame(
                igdb_game_id=game.id, name=game.name, total_rating=game.total_rating
            )
            if game.time_to_beat:
                igdb_game.time_to_beat = IgdbGameTimeToBeat(
                    igdb_game_time_to_beat_id=game.time_to_beat.id,
                    igdb_game_id=game.id,
                    normally=game.time_to_beat.normally,
                )
            for steam_game in game.external_games:
                external_game = IgdbExternalGame(
                    igdb_external_game_id=steam_game.id,
                    uid=int(steam_game.uid),
                    igdb_external_game_source_id=1,
                )
                igdb_game.external_games.append(external_game)
            games_to_add.append(igdb_game)

        self.db.add_all(games_to_add)
        self.db.commit()

        return CreateMyBacklogResponse(backlog_id=backlog.backlog_id)
