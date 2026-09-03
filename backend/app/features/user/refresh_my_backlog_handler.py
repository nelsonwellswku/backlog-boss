from fastapi import HTTPException, status
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
from app.features.user.cover_fetcher import CoverFetcherDep
from app.features.user.genre_fetcher import GenreFetcherDep
from app.features.user.platform_fetcher import PlatformFetcherDep
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
        current_user: RequiredCurrentUser,
        igdb_client: IgdbClientDep,
        cover_fetcher: CoverFetcherDep,
        genre_fetcher: GenreFetcherDep,
        platform_fetcher: PlatformFetcherDep,
    ):
        self.db = db
        self.steam = steam
        self.current_user = current_user
        self.igdb_client = igdb_client
        self.cover_fetcher = cover_fetcher
        self.genre_fetcher = genre_fetcher
        self.platform_fetcher = platform_fetcher

    def handle(self) -> RefreshMyBacklogResponse:
        """Refresh the user's backlog with newly owned Steam games.

        Syncs ownership for all owned games, fetches IGDB data for new
        games, and adds any newly qualified games to the backlog.
        """
        stmt = select(Backlog).where(
            Backlog.app_user_id == self.current_user.app_user_id
        )
        backlog = self.db.scalars(stmt).one_or_none()
        if not backlog:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Backlog not found. Create one first.",
            )

        # 1. Fetch owned games from Steam
        owned_games = self.steam.get_owned_games(self.current_user.steam_id)
        owned_game_steam_ids = {game.steam_game_id for game in owned_games}

        # 2. Find which owned games are not yet tracked as owned
        stmt = select(UserOwnedGame.igdb_game_id).where(
            UserOwnedGame.app_user_id == self.current_user.app_user_id
        )
        existing_owned_ids = set(self.db.scalars(stmt).all())

        # Build steam_id -> igdb_game_id mapping from IgdbExternalGame
        stmt = select(IgdbExternalGame.igdb_game_id, IgdbExternalGame.uid).where(
            IgdbExternalGame.uid.in_(owned_game_steam_ids)
        )
        igdb_mappings = self.db.execute(stmt).all()
        steam_to_igdb = {mapping.uid: mapping.igdb_game_id for mapping in igdb_mappings}

        # Find Steam games that need IGDB resolution
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
        # existing_owned_ids was loaded in step 2 — no per-row SELECT needed.
        # newly_queued tracks igdb_game_ids added in this session to avoid
        # duplicates when multiple Steam games map to the same IGDB game.
        newly_queued: set[int] = set()
        for steam_id in owned_game_steam_ids:
            igdb_game_id = steam_to_igdb.get(steam_id)
            if (
                igdb_game_id
                and igdb_game_id not in existing_owned_ids
                and igdb_game_id not in newly_queued
            ):
                ownership = UserOwnedGame(
                    app_user_id=self.current_user.app_user_id,
                    igdb_game_id=igdb_game_id,
                )
                self.db.add(ownership)
                newly_queued.add(igdb_game_id)

        # 5. Query qualified games via UserOwnedGame
        stmt = (
            select(IgdbGame)
            .join(UserOwnedGame, UserOwnedGame.igdb_game_id == IgdbGame.igdb_game_id)
            .where(UserOwnedGame.app_user_id == self.current_user.app_user_id)
            .where(IgdbGame.time_to_beat != None)  # noqa: E711
            .where(IgdbGame.total_rating != None)  # noqa: E711
            .distinct()
        )
        qualified_games = self.db.scalars(stmt).all()
        qualified_igdb_game_ids = {g.igdb_game_id for g in qualified_games}

        # Intentionally includes removed_on rows so previously removed games
        # are treated as "already in backlog" and won't be re-added.
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

        stmt = select(BacklogGame.igdb_game_id).where(
            BacklogGame.backlog_id == backlog.backlog_id
        )
        all_backlog_game_ids = list(self.db.scalars(stmt).all())

        self.cover_fetcher.fetch_and_persist(all_backlog_game_ids)
        self.genre_fetcher.fetch_and_persist(all_backlog_game_ids)
        self.platform_fetcher.fetch_and_persist(all_backlog_game_ids)

        self.db.commit()

        return RefreshMyBacklogResponse(
            backlog_id=backlog.backlog_id,
            games_added_count=len(new_backlog_games),
        )
