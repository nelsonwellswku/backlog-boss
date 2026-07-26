# Synchronous Backlog Refresh — Technical Implementation Plan

## Goal

Move cover image and genre fetching from background tasks into the synchronous refresh handler so that when the user clicks "Refresh Backlog," all data (Steam imports, covers, genres) is fully populated before the response returns, and the frontend's automatic refetch shows a complete view.

## Current State

- `POST /api/user/refresh-my-backlog` calls `RefreshMyBacklogHandler.handle()` synchronously (Steam sync + backlog insert), then the router enqueues two `BackgroundTasks` for covers and genres — `backend/app/features/user/user_router.py:46-52`.
- `fetch_missing_covers_task` creates its own DB session and `IgdbClient`, queries backlog games with `cover_image_id IS NULL`, fetches from IGDB, and updates — `backend/app/features/user/fetch_missing_covers_task.py`.
- `fetch_missing_genres_task` same pattern for genres — `backend/app/features/user/fetch_missing_genres_task.py`.
- Both task files wrap everything in try/except, logging errors silently so failures never surface to the user.
- `RefreshMyBacklogHandler` accepts `DbSession`, `SteamClientDep`, `RequiredCurrentUser`, `IgdbClientDep` via constructor injection — `backend/app/features/user/refresh_my_backlog_handler.py`.
- The handler calls `self.db.commit()` at line 85 (before the background tasks would run).
- Frontend `useRefreshMyBacklog` mutation invalidates `["myBacklog"]` query key on success — `frontend/src/hooks/useRefreshMyBacklog.ts:11`. The backlog page refetches automatically.
- `IgdbGame.genres` uses `lazy="raise"` — any access requires `selectinload` — `backend/app/database/models.py:96-98`.

## Files to Modify/Create

| File | Action |
|------|--------|
| `backend/app/features/user/cover_fetcher.py` | Create — `CoverFetcher` service class |
| `backend/app/features/user/genre_fetcher.py` | Create — `GenreFetcher` service class |
| `backend/app/features/user/refresh_my_backlog_handler.py` | Modify — add `CoverFetcher`/`GenreFetcher` deps, move commit to end |
| `backend/app/features/user/user_router.py` | Modify — remove `BackgroundTasks` and background task calls |
| `backend/app/features/user/fetch_missing_covers_task.py` | Delete — replaced by `CoverFetcher` |
| `backend/app/features/user/fetch_missing_genres_task.py` | Delete — replaced by `GenreFetcher` |
| `backend/tests/features/user/test_cover_fetcher.py` | Create — tests for `CoverFetcher` |
| `backend/tests/features/user/test_genre_fetcher.py` | Create — tests for `GenreFetcher` |
| `backend/tests/features/user/test_refresh_my_backlog_handler.py` | Modify — mock the two new fetchers |

## Step-by-Step Instructions

### Step 1 — Create `CoverFetcher`

Create `backend/app/features/user/cover_fetcher.py`:

```python
from logging import getLogger

from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import IgdbGame
from app.infrastructure.igdb_client import IgdbClientDep

logger = getLogger(__name__)


class CoverFetcher:
    def __init__(self, db: DbSession, igdb_client: IgdbClientDep):
        self.db = db
        self.igdb_client = igdb_client

    def fetch(self, game_ids: list[int]) -> None:
        stmt = select(IgdbGame.igdb_game_id).where(
            IgdbGame.igdb_game_id.in_(game_ids),
            IgdbGame.cover_image_id.is_(None),
        )
        missing_ids = list(self.db.scalars(stmt).all())

        if not missing_ids:
            logger.info("No games missing covers among %d provided", len(game_ids))
            return

        covers = self.igdb_client.get_covers_by_game_ids(missing_ids)

        if not covers:
            logger.info(
                "IGDB returned no covers for %d games", len(missing_ids)
            )
            return

        updated = 0
        for igdb_game_id, image_id in covers.items():
            game = self.db.get(IgdbGame, igdb_game_id)
            if game and game.cover_image_id is None:
                game.cover_image_id = image_id
                updated += 1

        logger.info("Updated covers for %d games", updated)
```

Key details:
- Uses injected `db` and `igdb_client` (no self-created sessions or clients).
- Filters the provided `game_ids` to only those still missing covers — handles the case where some already have covers from a previous run.
- Does NOT call `self.db.commit()` — the calling handler owns the transaction.
- No try/except — exceptions propagate to the caller (intentional: fail the whole refresh).

### Step 2 — Create `GenreFetcher`

Create `backend/app/features/user/genre_fetcher.py`:

```python
from logging import getLogger

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.engine import DbSession
from app.database.models import IgdbGame, IgdbGameGenre, IgdbGenre
from app.infrastructure.igdb_client import IgdbClientDep

logger = getLogger(__name__)


class GenreFetcher:
    def __init__(self, db: DbSession, igdb_client: IgdbClientDep):
        self.db = db
        self.igdb_client = igdb_client

    def fetch(self, game_ids: list[int]) -> None:
        stmt = select(IgdbGame.igdb_game_id).where(
            IgdbGame.igdb_game_id.in_(game_ids),
            ~select(IgdbGameGenre.igdb_game_id)
            .where(IgdbGameGenre.igdb_game_id == IgdbGame.igdb_game_id)
            .exists(),
        )
        missing_ids = list(self.db.scalars(stmt).all())

        if not missing_ids:
            logger.info("No games missing genres among %d provided", len(game_ids))
            return

        genres_by_game = self.igdb_client.get_genres_by_game_ids(missing_ids)

        if not genres_by_game:
            logger.info(
                "IGDB returned no genres for %d games", len(missing_ids)
            )
            return

        updated = 0
        for igdb_game_id, genre_list in genres_by_game.items():
            stmt = (
                select(IgdbGame)
                .where(IgdbGame.igdb_game_id == igdb_game_id)
                .options(selectinload(IgdbGame.genres))
            )
            game = self.db.scalars(stmt).one_or_none()
            if not game:
                continue

            for genre_response in genre_list:
                genre = self.db.get(IgdbGenre, genre_response.id)
                if not genre:
                    genre = IgdbGenre(
                        igdb_genre_id=genre_response.id,
                        name=genre_response.name,
                    )
                    self.db.add(genre)
                game.genres.append(genre)
                updated += 1

        logger.info("Updated genres for %d games", updated)
```

Key details:
- Uses `selectinload(IgdbGame.genres)` because `genres` has `lazy="raise"` on the model.
- Creates `IgdbGenre` rows on the fly if they don't already exist.
- Does NOT call `self.db.commit()` — the calling handler owns the transaction.
- No try/except — exceptions propagate to the caller.

### Step 3 — Modify `RefreshMyBacklogHandler`

In `backend/app/features/user/refresh_my_backlog_handler.py`:

**Changes:**
1. Add `CoverFetcher` and `GenreFetcher` imports and constructor params.
2. Remove the mid-method `self.db.commit()` call.
3. After adding backlog games, query all backlog game IDs.
4. Call `cover_fetcher.fetch()` and `genre_fetcher.fetch()`.
5. Commit once at the end.

```python
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import (
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
)
from app.features.api_model import ApiResponseModel
from app.features.auth.get_current_user import RequiredCurrentUser
from app.features.game.persist_igdb_games import persist_igdb_games
from app.features.user.cover_fetcher import CoverFetcher
from app.features.user.genre_fetcher import GenreFetcher
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
        cover_fetcher: CoverFetcher,
        genre_fetcher: GenreFetcher,
    ):
        self.db = db
        self.steam = steam
        self.current_user = current_user
        self.igdb_client = igdb_client
        self.cover_fetcher = cover_fetcher
        self.genre_fetcher = genre_fetcher

    def handle(self) -> RefreshMyBacklogResponse:
        # ... existing code to find backlog, fetch Steam games,
        # persist new IGDB games, find qualifying games,
        # compute to_add_igdb_game_ids, create BacklogGame rows ...

        self.db.add_all(new_backlog_games)

        # Query all backlog game IDs for cover/genre fetching
        stmt = select(BacklogGame.igdb_game_id).where(
            BacklogGame.backlog_id == backlog.backlog_id
        )
        all_backlog_game_ids = list(self.db.scalars(stmt).all())

        self.cover_fetcher.fetch(all_backlog_game_ids)
        self.genre_fetcher.fetch(all_backlog_game_ids)

        self.db.commit()

        return RefreshMyBacklogResponse(
            backlog_id=backlog.backlog_id,
            games_added_count=len(new_backlog_games),
        )
```

Full file after edits (replace entire contents):

```python
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import (
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
)
from app.features.api_model import ApiResponseModel
from app.features.auth.get_current_user import RequiredCurrentUser
from app.features.game.persist_igdb_games import persist_igdb_games
from app.features.user.cover_fetcher import CoverFetcher
from app.features.user.genre_fetcher import GenreFetcher
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
        cover_fetcher: CoverFetcher,
        genre_fetcher: GenreFetcher,
    ):
        self.db = db
        self.steam = steam
        self.current_user = current_user
        self.igdb_client = igdb_client
        self.cover_fetcher = cover_fetcher
        self.genre_fetcher = genre_fetcher

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

        stmt = select(BacklogGame.igdb_game_id).where(
            BacklogGame.backlog_id == backlog.backlog_id
        )
        all_backlog_game_ids = list(self.db.scalars(stmt).all())

        self.cover_fetcher.fetch(all_backlog_game_ids)
        self.genre_fetcher.fetch(all_backlog_game_ids)

        self.db.commit()

        return RefreshMyBacklogResponse(
            backlog_id=backlog.backlog_id,
            games_added_count=len(new_backlog_games),
        )
```

### Step 4 — Simplify the router

In `backend/app/features/user/user_router.py`:

**Changes:**
- Remove `BackgroundTasks` import.
- Remove `fetch_missing_covers_task` and `fetch_missing_genres_task` imports.
- Remove `bg_tasks` parameter and `add_task` calls.

```python
from fastapi import APIRouter, Depends

from app.features.user.get_me_handler import GetMeHandler, GetMeResponse
from app.features.user.get_my_backlog_handler import (
    GetMyBacklogHandler,
    GetMyBacklogResponse,
)
from app.features.user.refresh_my_backlog_handler import (
    RefreshMyBacklogHandler,
    RefreshMyBacklogResponse,
)

user_router = APIRouter(tags=["User"])


@user_router.get("/api/user/me")
def get_me(handler: GetMeHandler = Depends()) -> GetMeResponse | None:
    return handler.handle()


@user_router.post("/api/user/create-my-backlog")
def create_my_backlog(
    handler: CreateMyBacklogHandler = Depends(),
) -> CreateMyBacklogResponse:
    return handler.handle()


@user_router.get("/api/user/get-my-backlog")
def get_my_backlog(
    handler: GetMyBacklogHandler = Depends(),
) -> GetMyBacklogResponse:
    return handler.handle()


@user_router.post("/api/user/refresh-my-backlog")
def refresh_my_backlog(
    handler: RefreshMyBacklogHandler = Depends(),
) -> RefreshMyBacklogResponse:
    return handler.handle()
```

Also remove unused imports for `CreateMyBacklogHandler`/`CreateMyBacklogResponse` if they were only used in the router (check — they're used by the `create_my_backlog` route above, so keep them).

The full router file should keep only these imports:
- `APIRouter`, `Depends` from `fastapi`
- All handler/response classes used by the routes

### Step 5 — Delete old task files

```bash
rm backend/app/features/user/fetch_missing_covers_task.py
rm backend/app/features/user/fetch_missing_genres_task.py
```

### Step 6 — Write tests for `CoverFetcher`

Create `backend/tests/features/user/test_cover_fetcher.py`:

```python
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import IgdbGame
from app.features.user.cover_fetcher import CoverFetcher


def _create_game(
    db_session: Session,
    igdb_game_id: int,
    cover_image_id: str | None = None,
) -> IgdbGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=f"Game {igdb_game_id}",
        total_rating=80.0,
        cover_image_id=cover_image_id,
    )
    db_session.add(game)
    db_session.flush()
    return game


def test_fetch_updates_games_without_covers(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 1)
    _create_game(db_session, 2)
    _create_game(db_session, 3, cover_image_id="existing")
    db_session.commit()

    igdb_client = mocker.Mock()
    igdb_client.get_covers_by_game_ids.return_value = {1: "co1z2z", 2: "co4abc"}

    fetcher = CoverFetcher(db_session, igdb_client)
    fetcher.fetch([1, 2, 3])

    game_1 = db_session.get(IgdbGame, 1)
    game_2 = db_session.get(IgdbGame, 2)
    game_3 = db_session.get(IgdbGame, 3)

    assert game_1.cover_image_id == "co1z2z"
    assert game_2.cover_image_id == "co4abc"
    assert game_3.cover_image_id == "existing"

    igdb_client.get_covers_by_game_ids.assert_called_once_with([1, 2])


def test_fetch_skips_when_no_games_missing_covers(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 1, cover_image_id="c1")
    _create_game(db_session, 2, cover_image_id="c2")
    db_session.commit()

    igdb_client = mocker.Mock()

    fetcher = CoverFetcher(db_session, igdb_client)
    fetcher.fetch([1, 2])

    igdb_client.get_covers_by_game_ids.assert_not_called()


def test_fetch_handles_empty_game_list(
    db_session: Session,
    mocker: MockerFixture,
):
    igdb_client = mocker.Mock()

    fetcher = CoverFetcher(db_session, igdb_client)
    fetcher.fetch([])

    igdb_client.get_covers_by_game_ids.assert_not_called()
```

### Step 7 — Write tests for `GenreFetcher`

Create `backend/tests/features/user/test_genre_fetcher.py`:

```python
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import IgdbGame, IgdbGameGenre, IgdbGenre
from app.features.user.genre_fetcher import GenreFetcher
from app.infrastructure.igdb_client import GenreResponse


def _create_game(db_session: Session, igdb_game_id: int) -> IgdbGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=f"Game {igdb_game_id}",
        total_rating=80.0,
    )
    db_session.add(game)
    db_session.flush()
    return game


def test_fetch_updates_games_without_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_game(db_session, 1)
    _create_game(db_session, 2)

    game_3 = _create_game(db_session, 3)
    genre = IgdbGenre(igdb_genre_id=10, name="Action")
    db_session.add(genre)
    db_session.flush()
    game_3.genres.append(genre)
    db_session.commit()

    igdb_client = mocker.Mock()
    igdb_client.get_genres_by_game_ids.return_value = {
        1: [GenreResponse(id=10, name="Action"), GenreResponse(id=20, name="RPG")],
        2: [GenreResponse(id=30, name="Strategy")],
    }

    fetcher = GenreFetcher(db_session, igdb_client)
    fetcher.fetch([1, 2, 3])

    genres_1 = db_session.scalars(
        select(IgdbGenre.igdb_genre_id)
        .join(IgdbGameGenre)
        .where(IgdbGameGenre.igdb_game_id == 1)
    ).all()
    genres_2 = db_session.scalars(
        select(IgdbGenre.igdb_genre_id)
        .join(IgdbGameGenre)
        .where(IgdbGameGenre.igdb_game_id == 2)
    ).all()
    genres_3 = db_session.scalars(
        select(IgdbGenre.igdb_genre_id)
        .join(IgdbGameGenre)
        .where(IgdbGameGenre.igdb_game_id == 3)
    ).all()

    assert sorted(genres_1) == [10, 20]
    assert sorted(genres_2) == [30]
    assert genres_3 == [10]

    igdb_client.get_genres_by_game_ids.assert_called_once_with([1, 2])


def test_fetch_skips_when_no_games_missing_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    game = _create_game(db_session, 1)
    genre = IgdbGenre(igdb_genre_id=10, name="Action")
    db_session.add(genre)
    db_session.flush()
    game.genres.append(genre)
    db_session.commit()

    igdb_client = mocker.Mock()

    fetcher = GenreFetcher(db_session, igdb_client)
    fetcher.fetch([1])

    igdb_client.get_genres_by_game_ids.assert_not_called()


def test_fetch_handles_empty_game_list(
    db_session: Session,
    mocker: MockerFixture,
):
    igdb_client = mocker.Mock()

    fetcher = GenreFetcher(db_session, igdb_client)
    fetcher.fetch([])

    igdb_client.get_genres_by_game_ids.assert_not_called()
```

### Step 8 — Update `test_refresh_my_backlog_handler.py`

Add `CoverFetcher` and `GenreFetcher` mocks to every test that creates `RefreshMyBacklogHandler`.

**Changes needed:**
- Each constructor call like `RefreshMyBacklogHandler(db_session, steam_client, current_user, igdb_client)` needs two more args: `cover_fetcher=mocker.Mock(), genre_fetcher=mocker.Mock()`.

**Example updated test:**

```python
def test_handle_raises_not_found_when_backlog_is_missing(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    steam_client = mocker.Mock()
    igdb_client = mocker.Mock()
    handler = RefreshMyBacklogHandler(
        db_session, steam_client, current_user, igdb_client,
        mocker.Mock(), mocker.Mock(),
    )
    # ... rest unchanged
```

For the tests that verify games are added (e.g., `test_handle_adds_qualifying_new_game_skips_active_game`), additionally verify that the fetchers were called with the correct game IDs:

```python
def test_handle_adds_qualifying_new_game_skips_active_game(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    backlog = _create_backlog(db_session, current_user)
    existing_game = _create_game(db_session, 1, "Existing Game", 111)
    _create_game(db_session, 2, "New Game", 222)
    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=existing_game.igdb_game_id,
    )
    db_session.add(backlog_game)
    db_session.commit()

    steam_client = mocker.Mock()
    steam_client.get_owned_games.return_value = [
        SteamGame(steam_game_id=111),
        SteamGame(steam_game_id=222),
    ]
    cover_fetcher = mocker.Mock()
    genre_fetcher = mocker.Mock()
    handler = RefreshMyBacklogHandler(
        db_session, steam_client, current_user, mocker.Mock(),
        cover_fetcher, genre_fetcher,
    )

    actual = handler.handle()

    assert actual.backlog_id == backlog.backlog_id
    assert actual.games_added_count == 1

    cover_fetcher.fetch.assert_called_once_with([1, 2])
    genre_fetcher.fetch.assert_called_once_with([1, 2])
```

Apply this pattern to all existing tests — every `RefreshMyBacklogHandler` instantiation needs the two new mock args.

### Step 9 — Verify

```bash
cd backend
uv run ruff check . && uv run ruff format .
uv run pytest -q
```

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Service class DI pattern | `CoverFetcher`/`GenreFetcher` as FastAPI-injectable classes | Follows existing handler DI pattern; keeps services testable without mocking constructors at module level |
| Method signature | `.fetch(game_ids: list[int])` | Backlog-agnostic — reusable for any set of games, not coupled to backlog concept |
| Transaction strategy | Single commit at end (all-or-nothing) | If covers or genres fail, the entire refresh rolls back. User retries cleanly. No partial state. |
| Error handling | Let exceptions propagate | User sees an error on IGDB failure and can retry. Simpler than silent background failures. |
| Scope of fetch | All games in backlog | Handles edge cases where games were previously added without covers/genres (e.g., from before this feature shipped, or from transient IGDB failures) |
| No `selectinload` for covers | `db.get(IgdbGame, id)` | `cover_image_id` is a direct column, not a relationship — no lazy loading issue |
| `selectinload` for genres | `select(IgdbGame).options(selectinload(IgdbGame.genres))` | `IgdbGame.genres` has `lazy="raise"` — must explicitly load before appending |
| No changes to `CreateMyBacklogHandler` | Leave as-is | The create flow is a one-time operation; covers/genres will be fetched on the first refresh |
| No frontend changes | Invalidation already works | `useRefreshMyBacklog` invalidates `["myBacklog"]` on success, refetch gets fully populated data |

## Edge Cases

- **IGDB API failure**: Exception propagates to FastAPI, which returns a 500 error. The user sees a failure state and can retry. No partial writes — the entire refresh is rolled back.
- **Empty backlog (no games)**: Both fetchers receive an empty list and return immediately — no IGDB calls made.
- **All games already have covers/genres**: The fetchers query first to find which of the given `game_ids` actually need work. If none, no IGDB call is made.
- **Game has cover but no genres (or vice versa)**: Each fetcher operates independently on the same game list. One fetcher may do work while the other skips.
- **Concurrent refreshes**: With all-or-nothing transactions, concurrent requests won't conflict. Both run independently; whichever commits second sees the other's committed data at read time.
- **Genre already exists**: `GenreFetcher` checks `db.get(IgdbGenre, id)` before creating — no duplicate genre rows.
- **Removed games in backlog**: `BacklogGame` rows with `removed_on` set are still returned by the backlog game ID query. This is the same behavior as before (the old task used `join(BacklogGame)` without filtering on `removed_on`). The handler's "already exists" check at step 5 also includes removed games (using `select(...)` without a `removed_on` filter), so a removed game won't be re-added, but its cover/genre may still be fetched. This is harmless — the cover/genre data exists on the `IgdbGame` row regardless of backlog status.
