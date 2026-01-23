from pydantic import BaseModel, Field
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import Backlog, BacklogGame, Game
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
        stmt = select(Game.steam_id).where(Game.steam_id.in_(owned_game_steam_ids))
        games_in_db = self.db.scalars(stmt).all()
        games_in_db_ids = set(games_in_db)

        game_ids_to_insert = owned_game_steam_ids - games_in_db_ids

        # fetch the games to insert from igdb and save them to the database
        igdb_games = self.igdb_client.get_games(
            game_ids_to_insert, len(game_ids_to_insert)
        )

        # we need to double check that the games we get back are not already in the db
        # this is because when querying igdb for steam games, igdb will sometimes return
        # two steam ids for a singular igdb id - one of these we'll _never_ insert
        stmt = select(Game.igdb_id).where(
            Game.igdb_id.in_([game.igdb_game_id for game in igdb_games])
        )
        igdb_ids_to_preclude_from_insert = set(self.db.scalars(stmt).all())

        games_to_insert = [
            Game(
                title=game.title,
                igdb_id=game.igdb_game_id,
                steam_id=game.steam_game_id,
                total_rating=game.total_rating,
                time_to_beat=game.time_to_beat,
            )
            for game in igdb_games
            if game.igdb_game_id not in igdb_ids_to_preclude_from_insert
        ]

        self.db.add_all(games_to_insert)
        self.db.flush()

        # re-query owned games by steam id in case a subset of the user's owned games
        # already existed in the database when we inserted new Game records above
        stmt = select(Game).where(Game.steam_id.in_(owned_game_steam_ids))
        games_to_add_to_backlog = self.db.scalars(stmt).all()

        backlog_games = [
            BacklogGame(backlog=backlog, game=game) for game in games_to_add_to_backlog
        ]
        self.db.add(backlog)
        self.db.add_all(backlog_games)

        self.db.commit()

        return CreateMyBacklogResponse(backlog_id=backlog.backlog_id)
