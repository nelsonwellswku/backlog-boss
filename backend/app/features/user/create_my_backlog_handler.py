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


class CreateMyBacklogResponse(ApiResponseModel):
    backlog_id: int


class CreateMyBacklogHandler:
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
    def handle(self) -> CreateMyBacklogResponse:
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
        igdb_games = self.igdb_client.get_games_by_steam_id(steam_game_ids_to_insert)
        persist_igdb_games(self.db, igdb_games)

        # get all the steam games (and thus igdb games) the user owns
        # and add them to the backlog
        # do this in case the game already existed in the database
        # additionally, only for the ones that have ratings and times
        stmt = (
            select(IgdbGame)
            .join(IgdbExternalGame)
            .where(IgdbExternalGame.uid.in_(owned_game_steam_ids))
            .where(IgdbGame.time_to_beat != None)  # noqa: E711
            .where(IgdbGame.total_rating != None)  # noqa: E711
            .distinct()
        )

        owned_games_to_add_to_backlog = self.db.scalars(stmt).all()

        backlog_games = [
            BacklogGame(igdb_game_id=og.igdb_game_id, backlog_id=backlog.backlog_id)
            for og in owned_games_to_add_to_backlog
        ]

        backlog.backlog_games.extend(backlog_games)
        self.db.add(backlog)
        self.db.commit()

        return CreateMyBacklogResponse(backlog_id=backlog.backlog_id)
