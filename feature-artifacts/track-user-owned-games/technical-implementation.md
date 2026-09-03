# Track User Owned Games — Technical Implementation Plan

## Goal

Create a `UserOwnedGame` table that records every Steam-owned game for each user, serving as the foundational ownership data layer independent of the backlog quality gate.

## Current State

- `CreateMyBacklogHandler` (`backend/app/features/user/create_my_backlog_handler.py:39-92`) fetches Steam games, queries `IgdbExternalGame.uid` to diff which games need IGDB resolution, then adds qualified games (with rating + time_to_beat) to the backlog. Returns early if backlog already exists (line 46-47).
- `RefreshMyBacklogHandler` (`backend/app/features/user/refresh_my_backlog_handler.py:45-113`) follows the same pattern: fetch Steam → diff via `IgdbExternalGame` → persist new IGDB data → add qualified games to backlog.
- Both handlers use `IgdbExternalGame.uid` (line 56-60 in create, line 59-63 in refresh) as the source of truth for "which Steam games have been processed." This conflates ownership tracking with IGDB resolution status.
- `IgdbGame` (`backend/app/database/models.py:88-109`) stores game metadata. `IgdbExternalGame` (line 148-167) maps IGDB games to external platform IDs (Steam appids via `uid` column, source_id=1).
- `persist_igdb_games` (`backend/app/features/game/persist_igdb_games.py`) creates `IgdbGame`, `IgdbExternalGame`, and related rows. Uses `db.flush()` — caller commits. No changes needed to this function.
- No ownership model exists today. Ownership is derived at runtime by comparing Steam IDs against `IgdbExternalGame.uid`.
- Latest migration is `0013.sql` (adds `Year` column to `IgdbExternalGame`). Next is `0014.sql`.

## Files to Modify/Create

| File | Action |
|------|--------|
| `migrations/up/0014.sql` | Create — `bb.UserOwnedGame` table |
| `backend/app/database/models.py` | Modify — add `UserOwnedGame` ORM model |
| `backend/app/features/user/create_my_backlog_handler.py` | Modify — insert ownership, query `UserOwnedGame` for backlog join |
| `backend/app/features/user/refresh_my_backlog_handler.py` | Modify — insert ownership, query `UserOwnedGame` for diff and backlog join |

## Step-by-Step Instructions

### Step 1 — Create migration `0014.sql`

Create `migrations/up/0014.sql`:

```sql
create table bb.UserOwnedGame (
    UserOwnedGameId int identity(1,1) primary key,
    AppUserId int not null foreign key references bb.AppUser(AppUserId),
    IgdbGameId int not null foreign key references bb.IgdbGame(Id),
    constraint UQ_UserOwnedGame_User_Game unique (AppUserId, IgdbGameId)
);
```

Key details:
- The unique constraint on `(AppUserId, IgdbGameId)` prevents duplicate ownership entries and also creates an index for the primary query pattern (lookup by user)
- No additional indexes needed — the unique constraint covers the query patterns used by both handlers
- Uses `identity(1,1)` for auto-increment PK, consistent with existing migrations

### Step 2 — Add `UserOwnedGame` ORM model

In `backend/app/database/models.py`, add the following class (e.g., after `BacklogGame` around line 86):

```python
class UserOwnedGame(Base):
    __tablename__ = "UserOwnedGame"

    user_owned_game_id: Mapped[int] = mapped_column(
        "UserOwnedGameId", primary_key=True
    )
    app_user_id: Mapped[int] = mapped_column(
        "AppUserId", ForeignKey("bb.AppUser.AppUserId")
    )
    igdb_game_id: Mapped[int] = mapped_column(
        "IgdbGameId", ForeignKey("bb.IgdbGame.Id")
    )

    app_user: Mapped["AppUser"] = relationship("AppUser", lazy="raise")
    igdb_game: Mapped["IgdbGame"] = relationship("IgdbGame", lazy="raise")
```

Key details:
- `lazy="raise"` on both relationships prevents accidental eager loading — matches the convention used by `BacklogGame` (line 82-85)
- No back_populates needed — `AppUser` and `IgdbGame` don't need to know about ownership collections
- Column names match the migration exactly (PascalCase in DB, snake_case in Python)

### Step 3 — Refactor `CreateMyBacklogHandler`

Replace the contents of `backend/app/features/user/create_my_backlog_handler.py` with:

```python
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
        igdb_mappings = self.db.scalars(stmt).all()

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
            igdb_mappings = self.db.scalars(stmt).all()
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
```

Key details:
- Ownership is tracked via a batch-loaded set (`existing_owned_ids`) — no per-row SELECT queries in the insertion loop
- The ownership insertion loop iterates over all owned Steam games, inserting `UserOwnedGame` rows for games not already tracked
- The backlog join now goes through `UserOwnedGame` instead of `IgdbExternalGame`
- Early return preserved — ownership only synced on first backlog creation
- `IgdbExternalGame` is still queried to build the `steam_to_igdb` mapping needed for inserting `UserOwnedGame` rows (we need to know which `igdb_game_id` corresponds to each Steam `appid`)
- The `IgdbExternalGame` query fetches `(igdb_game_id, uid)` pairs rather than just `uid` to build the mapping

### Step 4 — Refactor `RefreshMyBacklogHandler`

Replace the contents of `backend/app/features/user/refresh_my_backlog_handler.py` with:

```python
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
        igdb_mappings = self.db.scalars(stmt).all()
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
            igdb_mappings = self.db.scalars(stmt).all()
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
```

Key details:
- Same ownership sync pattern as `CreateMyBacklogHandler`: fetch Steam → insert ownership → fetch IGDB for new → add to backlog
- The refresh handler does NOT have an early return for ownership — it always syncs ownership, even on subsequent refreshes
- The diff for "which games need IGDB data" uses `IgdbExternalGame` (via `steam_to_igdb` mapping) — this is separate from the ownership diff
- The backlog join uses `UserOwnedGame` instead of `IgdbExternalGame`
- Ownership insertion uses the same batch-loaded set approach as `CreateMyBacklogHandler` — no per-row SELECT queries

### Step 5 — Verify

```bash
cd backend
uv run ruff check . && uv run ruff format .
uv run pytest -q
```

Key things to verify:
- Lint and format pass with no errors
- All existing tests pass (tests use real SQL Server via Testcontainers)
- The migration applies cleanly when `docker compose up` is run

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Ownership as source of truth | `UserOwnedGame` replaces `IgdbExternalGame` for ownership tracking | Separates "what does the user own" from "have we fetched IGDB data" — cleaner semantics |
| Early return preserved | Keep early return in `CreateMyBacklogHandler` | Issue explicitly states ownership is only synced on first creation; existing users handled separately later |
| Diff for IGDB fetch | `IgdbExternalGame` mapping (steam_id → igdb_game_id) | Still needed to build the mapping for `UserOwnedGame` insertion; not replaced by `UserOwnedGame` |
| Backlog join | `UserOwnedGame` → `IgdbGame` | Semantically clearer ("games the user owns that qualify"); removes `IgdbExternalGame` dependency from backlog logic |
| Insertion strategy | Batch-loaded set + conditional insert | Avoids N+1 queries; portable across DB dialects; clear "append-only" semantics |
| `persist_igdb_games` | No changes | Remains focused on IGDB data persistence; ownership is handled at handler level |
| ORM relationships | `lazy="raise"` on `UserOwnedGame` relationships | Prevents accidental eager loading; matches convention of `BacklogGame` |

## Edge Cases

- **Existing users without ownership data**: The early return in `CreateMyBacklogHandler` means users who created their backlog before this feature won't have `UserOwnedGame` rows until they call refresh. This is acceptable — noted in the issue as "a foundation, not critical data."
- **Concurrent refreshes**: The unique constraint on `(AppUserId, IgdbGameId)` prevents duplicate ownership entries. The batch-loaded set ensures no duplicates are inserted within a single handler invocation. No additional locking needed.
- **Games without IGDB data**: Steam games that can't be resolved to IGDB (e.g., unknown games) won't have `IgdbExternalGame` rows, so they won't get `UserOwnedGame` entries either. This is correct — we can't track ownership of games we can't identify in IGDB.
- **Games with IGDB data but no rating/time_to_beat**: These get `UserOwnedGame` entries (owned) but are NOT added to the backlog. This is the core behavior — ownership is tracked regardless of quality gate.
- **Manually added games**: Adding a game via search does NOT create a `UserOwnedGame` entry. Only Steam-synced games get ownership records. This matches the acceptance criteria.
- **Append-only ownership**: `UserOwnedGame` entries are never deleted. Even if a user uninstalls a game on Steam, the ownership record persists. This is by design.
- **`IgdbExternalGame` still needed**: The `IgdbExternalGame` query is still required to build the `steam_id → igdb_game_id` mapping for inserting `UserOwnedGame` rows. We can't avoid this — `UserOwnedGame` stores `igdb_game_id`, not `steam_id`.
