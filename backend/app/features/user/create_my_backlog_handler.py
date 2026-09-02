from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import (
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
    UserOwnedGame,
)
from app.features.api_model import ApiResponseModel
from app.features.auth.get_current_user import RequiredCurrentUser
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
        current_user: RequiredCurrentUser,
        igdb_client: IgdbClientDep,
    ):
        self.db = db
        self.steam = steam
        self.current_user = current_user
        self.igdb_client = igdb_client

    def handle(self) -> CreateMyBacklogResponse:
        """Create a user's backlog from their Steam library.

        Persists ownership for all owned games, fetches IGDB data for new
        games, and adds qualified games (with rating and time-to-beat) to
        the backlog. Returns early if the user already has a backlog.
        """
        stmt = select(Backlog).where(
            Backlog.app_user_id == self.current_user.app_user_id
        )
        backlog = self.db.scalars(stmt).one_or_none()
        if backlog:
            return CreateMyBacklogResponse(backlog_id=backlog.backlog_id)

        backlog = Backlog(app_user_id=self.current_user.app_user_id)

        # 1. Fetch owned games from Steam
        owned_games = self.steam.get_owned_games(self.current_user.steam_id)
        owned_game_steam_ids = {game.steam_game_id for game in owned_games}

        # 2. Find which owned games are not yet tracked as owned
        stmt = select(UserOwnedGame.igdb_game_id).where(
            UserOwnedGame.app_user_id == self.current_user.app_user_id
        )
        existing_owned_ids = set(self.db.scalars(stmt).all())

        # We need to find the IGDB game IDs for owned Steam games that
        # are already in the DB (via IgdbExternalGame) to compare against
        # existing ownership records
        stmt = select(IgdbExternalGame.igdb_game_id, IgdbExternalGame.uid).where(
            IgdbExternalGame.uid.in_(owned_game_steam_ids)
        )
        igdb_mappings = self.db.execute(stmt).all()

        # Build a map of steam_id -> igdb_game_id for games already in DB
        steam_to_igdb = {}
        for mapping in igdb_mappings:
            steam_to_igdb[mapping.uid] = mapping.igdb_game_id

        # Find Steam games that need IGDB resolution (not in IgdbExternalGame)
        steam_ids_needing_igdb = owned_game_steam_ids - set(steam_to_igdb.keys())

        # 3. Fetch IGDB data for new games
        if steam_ids_needing_igdb:
            igdb_games = self.igdb_client.get_games_by_steam_id(steam_ids_needing_igdb)
            persist_igdb_games(self.db, igdb_games)

            # Refresh mappings after persist
            stmt = select(IgdbExternalGame.igdb_game_id, IgdbExternalGame.uid).where(
                IgdbExternalGame.uid.in_(steam_ids_needing_igdb)
            )
            igdb_mappings = self.db.execute(stmt).all()
            for mapping in igdb_mappings:
                steam_to_igdb[mapping.uid] = mapping.igdb_game_id

        # 4. Insert ownership for ALL owned games not already tracked
        # existing_owned_ids was loaded in step 2 — no per-row SELECT needed
        for steam_id in owned_game_steam_ids:
            igdb_game_id = steam_to_igdb.get(steam_id)
            if igdb_game_id and igdb_game_id not in existing_owned_ids:
                ownership = UserOwnedGame(
                    app_user_id=self.current_user.app_user_id,
                    igdb_game_id=igdb_game_id,
                )
                self.db.add(ownership)

        # 5. Query qualified games via UserOwnedGame
        stmt = (
            select(IgdbGame)
            .join(UserOwnedGame, UserOwnedGame.igdb_game_id == IgdbGame.igdb_game_id)
            .where(UserOwnedGame.app_user_id == self.current_user.app_user_id)
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
