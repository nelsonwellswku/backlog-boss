# Refresh Backlog Genres — Technical Implementation Plan

## Goal

When the "Refresh Backlog" button is pressed, enqueue a FastAPI `BackgroundTask` that fetches genre data from IGDB for any games in the user's backlog where the `IgdbGameGenre` association table has no rows. The refresh response returns immediately; the genre fetch happens asynchronously.

## Current State

- `POST /api/user/refresh-my-backlog` triggers `RefreshMyBacklogHandler.handle()` which syncs new Steam games and returns `{ backlog_id, games_added_count }`.
- After the handler completes, `bg_tasks.add_task(fetch_missing_covers_task, result.backlog_id)` runs in the background — `backend/app/features/user/user_router.py:48`.
- `IgdbGame.genres` is a many-to-many relationship via `IgdbGameGenre` — `backend/app/database/models.py:96-98`.
- `IgdbGameGenre` is the association table with `igdb_game_id` and `igdb_genre_id` — `backend/app/database/models.py:109-116`.
- `IgdbGenre` has `igdb_genre_id` and `name` — `backend/app/database/models.py:101-106`.
- `IgdbClient` already fetches genres as part of `get_games_by_steam_id()` (line 130) and `search_games_by_name()` (line 181), but there is no method to fetch genres for specific game IDs in isolation.
- `persist_igdb_games.py` stores genres at lines 82-87 when games are first added.
- `get_covers_by_game_ids()` (line 303-336) is the pattern to follow for the new IGDB method.

## Files to Modify/Create

| File | Action |
|------|--------|
| `backend/app/infrastructure/igdb_client.py` | Modify — add `get_genres_by_game_ids()` method |
| `backend/app/features/user/fetch_missing_genres_task.py` | Create — background task function |
| `backend/app/features/user/user_router.py` | Modify — import and enqueue genre fetch |
| `backend/tests/features/user/test_fetch_missing_genres_task.py` | Create — tests |

## Step-by-Step Instructions

### Step 1 — Add `get_genres_by_game_ids()` to `IgdbClient`

In `backend/app/infrastructure/igdb_client.py`, add a new method to `IgdbClient` after `get_covers_by_game_ids()` (after line 336):

```python
def get_genres_by_game_ids(self, game_ids: list[int]) -> dict[int, list[GenreResponse]]:
    if not game_ids:
        return {}

    formatted_ids = self._format_ids(game_ids)
    endpoint = "games"
    limit = 500
    offset = 0
    genres: dict[int, list[GenreResponse]] = {}

    while True:
        query = f"""
            fields id, genres.name;
            where id = ({formatted_ids}) & genres != null;
            offset {offset};
            limit {limit};
        """

        response_bytes = self._api_request(endpoint, query)
        response_json = json.loads(response_bytes)

        if not response_json:
            break

        for game in response_json:
            game_id = game["id"]
            if "genres" in game and game["genres"]:
                genres[game_id] = [
                    GenreResponse(id=g["id"], name=g["name"])
                    for g in game["genres"]
                ]

        if len(response_json) < limit:
            break

        offset += limit

    return genres
```

Key details:
- Queries the `games` endpoint filtered by IGDB game IDs
- Requests only `id` and `genres.name`
- Filters out games where `genres` is null at the query level (`& genres != null`)
- Batches in groups of 500 (IGDB max limit per request)
- Returns a `dict[int, list[GenreResponse]]` mapping `igdb_game_id → genres`
- Reuses existing `_format_ids()` and `_api_request()` methods

### Step 2 — Create the background task

Create `backend/app/features/user/fetch_missing_genres_task.py`:

```python
from logging import getLogger

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.engine import create_db_session
from app.database.models import BacklogGame, IgdbGame, IgdbGameGenre, IgdbGenre
from app.infrastructure.igdb_client import IgdbClient

logger = getLogger(__name__)


def fetch_missing_genres_task(backlog_id: int, db: Session | None = None) -> None:
    try:
        if db is not None:
            _run(backlog_id, db)
        else:
            with create_db_session() as session:
                _run(backlog_id, session)
    except Exception:
        logger.exception("Failed to fetch missing genres for backlog %d", backlog_id)


def _run(backlog_id: int, db: Session) -> None:
    # Find games in backlog that have no entries in IgdbGameGenre
    stmt = (
        select(IgdbGame.igdb_game_id)
        .join(BacklogGame)
        .where(BacklogGame.backlog_id == backlog_id)
        .where(
            ~select(IgdbGameGenre.igdb_game_id)
            .where(IgdbGameGenre.igdb_game_id == IgdbGame.igdb_game_id)
            .exists()
        )
    )
    game_ids = list(db.scalars(stmt).all())

    if not game_ids:
        logger.info("No games missing genres in backlog %d", backlog_id)
        return

    igdb_client = IgdbClient.create()
    genres_by_game = igdb_client.get_genres_by_game_ids(game_ids)

    if not genres_by_game:
        logger.info(
            "IGDB returned no genres for %d games in backlog %d",
            len(game_ids),
            backlog_id,
        )
        return

    updated = 0
    for igdb_game_id, genre_list in genres_by_game.items():
        # Re-check that the game still has no genres (defensive against race conditions)
        stmt = (
            select(IgdbGame)
            .where(IgdbGame.igdb_game_id == igdb_game_id)
            .where(
                ~select(IgdbGameGenre.igdb_game_id)
                .where(IgdbGameGenre.igdb_game_id == IgdbGame.igdb_game_id)
                .exists()
            )
        )
        game = db.scalars(stmt).one_or_none()
        if not game:
            continue

        # Fetch or create genre objects, then link them
        for genre_response in genre_list:
            genre = db.get(IgdbGenre, genre_response.id)
            if not genre:
                genre = IgdbGenre(
                    igdb_genre_id=genre_response.id,
                    name=genre_response.name,
                )
                db.add(genre)
            game.genres.append(genre)
            updated += 1

    db.commit()
    logger.info(
        "Updated genres for %d games in backlog %d",
        updated,
        backlog_id,
    )
```

Key details:
- Creates its own DB session via `create_db_session()` (the request session is closed by the time the background task runs)
- Creates its own `IgdbClient.create()` — FastAPI DI isn't available in background tasks
- Uses a `NOT EXISTS` subquery to find games with zero rows in `IgdbGameGenre`
- For each game, re-checks that it still has no genres before updating (defensive against race conditions)
- Fetches existing `IgdbGenre` objects via `db.get()` before creating new ones — avoids duplicate genre rows
- Wraps everything in try/except — logs exception and exits gracefully, never crashes the process
- Logs success with count of updated genre links

### Step 3 — Modify the router to enqueue the background task

In `backend/app/features/user/user_router.py`, add the import and task:

```python
from fastapi import APIRouter, BackgroundTasks, Depends

from app.features.user.create_my_backlog_handler import (
    CreateMyBacklogHandler,
    CreateMyBacklogResponse,
)
from app.features.user.fetch_missing_covers_task import (
    fetch_missing_covers_task,
)
from app.features.user.fetch_missing_genres_task import (
    fetch_missing_genres_task,
)
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
    bg_tasks: BackgroundTasks,
    handler: RefreshMyBacklogHandler = Depends(),
) -> RefreshMyBacklogResponse:
    result = handler.handle()
    bg_tasks.add_task(fetch_missing_covers_task, result.backlog_id)
    bg_tasks.add_task(fetch_missing_genres_task, result.backlog_id)
    return result
```

Key details:
- `BackgroundTasks` is already imported and injected
- `fetch_missing_genres_task` is called with `result.backlog_id` (available from the handler's response)
- The response returns immediately; both background tasks run after the response is sent
- No changes to `RefreshMyBacklogHandler` — it remains purely synchronous

### Step 4 — Write tests

Create `backend/tests/features/user/test_fetch_missing_genres_task.py`:

```python
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AppUser,
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
    IgdbGameGenre,
    IgdbGenre,
)
from app.features.user.fetch_missing_genres_task import (
    fetch_missing_genres_task,
)
from app.infrastructure.igdb_client import GenreResponse


def _create_app_user(db_session: Session) -> AppUser:
    app_user = AppUser(
        steam_id="76561198000000000",
        persona_name="Test Persona",
        first_name="Test",
        last_name="User",
    )
    db_session.add(app_user)
    db_session.flush()
    return app_user


def _create_backlog_game(
    db_session: Session,
    backlog: Backlog,
    igdb_game_id: int,
) -> BacklogGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=f"Game {igdb_game_id}",
        total_rating=80.0,
    )
    game.external_games.append(
        IgdbExternalGame(
            igdb_external_game_id=igdb_game_id + 1000,
            uid=igdb_game_id * 100,
            igdb_external_game_source_id=1,
        )
    )
    db_session.add(game)
    db_session.flush()

    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=game.igdb_game_id,
    )
    db_session.add(backlog_game)
    db_session.flush()
    return backlog_game


def test_fetch_missing_genres_updates_games_without_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()

    _create_backlog_game(db_session, backlog, 1)
    _create_backlog_game(db_session, backlog, 2)
    _create_backlog_game(db_session, backlog, 3)
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_genres_task.IgdbClient"
    )
    igdb_client_mock.create.return_value.get_genres_by_game_ids.return_value = {
        1: [GenreResponse(id=10, name="Action"), GenreResponse(id=20, name="RPG")],
        3: [GenreResponse(id=30, name="Strategy")],
    }

    fetch_missing_genres_task(backlog.backlog_id, db=db_session)

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
    assert genres_2 == []
    assert genres_3 == [30]


def test_fetch_missing_genres_skips_games_with_existing_genres(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()

    game_1 = IgdbGame(
        igdb_game_id=1,
        name="Game 1",
        total_rating=80.0,
    )
    genre = IgdbGenre(igdb_genre_id=10, name="Action")
    db_session.add(genre)
    db_session.flush()
    game_1.genres.append(genre)
    db_session.add(game_1)
    db_session.flush()

    backlog_game = BacklogGame(
        backlog_id=backlog.backlog_id,
        igdb_game_id=game_1.igdb_game_id,
    )
    db_session.add(backlog_game)
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_genres_task.IgdbClient"
    )

    fetch_missing_genres_task(backlog.backlog_id, db=db_session)

    igdb_client_mock.create.return_value.get_genres_by_game_ids.assert_not_called()


def test_fetch_missing_genres_handles_igdb_failure(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()

    _create_backlog_game(db_session, backlog, 1)
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_genres_task.IgdbClient"
    )
    igdb_client_mock.create.return_value.get_genres_by_game_ids.side_effect = Exception(
        "IGDB API error"
    )

    fetch_missing_genres_task(backlog.backlog_id, db=db_session)

    genres = db_session.scalars(
        select(IgdbGenre.igdb_genre_id)
        .join(IgdbGameGenre)
        .where(IgdbGameGenre.igdb_game_id == 1)
    ).all()
    assert genres == []


def test_fetch_missing_genres_empty_backlog(
    db_session: Session,
    mocker: MockerFixture,
):
    app_user = _create_app_user(db_session)
    backlog = Backlog(app_user_id=app_user.app_user_id)
    db_session.add(backlog)
    db_session.flush()
    db_session.commit()

    igdb_client_mock = mocker.patch(
        "app.features.user.fetch_missing_genres_task.IgdbClient"
    )

    fetch_missing_genres_task(backlog.backlog_id, db=db_session)

    igdb_client_mock.create.return_value.get_genres_by_game_ids.assert_not_called()
```

### Step 5 — Verify

```bash
cd backend
uv run ruff check . && uv run ruff format .
uv run pytest -q -k test_fetch_missing_genres
```

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Where to trigger background task | Router function, not handler | Keeps handler synchronous and testable; router is the orchestration layer |
| DB session in background task | `create_db_session()` (standalone) | Request session is closed before background task runs; need own session |
| IGDB client instantiation | `IgdbClient.create()` directly | FastAPI DI not available in background tasks; `create()` resolves from env vars |
| Error handling | try/except with logging | Background task failures should never affect the user; logs are sufficient for observability |
| Genre fetch scope | All games with no `IgdbGameGenre` rows | Simple approach; re-querying IGDB for games without genres is cheap and avoids tracking "attempted" state |
| IGDB query approach | New `get_genres_by_game_ids()` method | Separate from existing `get_games_by_steam_id()` — different endpoint, different fields, different purpose |
| Genre deduplication | `db.get(IgdbGenre, genre_id)` before insert | Avoids duplicate genre rows in the `IgdbGenre` table |
| Response model change | None | User doesn't need to know genres are being fetched; no new fields needed |

## Edge Cases

- **Race condition (multiple refreshes)**: The background task only updates games that have no `IgdbGameGenre` rows at the time of update. Two concurrent tasks will both run, but the second one will find nothing to update.
- **IGDB rate limits**: The background task queries IGDB in batches of 500. For a backlog of 500 games, this is a single request. Rate limits are unlikely to be hit in normal usage.
- **Games with no IGDB genres**: The IGDB query filters `genres != null` at the API level. Games without genres are simply not returned, and their genre associations stay empty.
- **New games added during refresh**: The background task runs after the sync completes, so it picks up any newly added games that are also missing genres.
- **Backlog deleted during background task**: The `select` query returns no results; the task exits early with a log message.
- **Existing genre rows in IgdbGenre**: The task uses `db.get(IgdbGenre, genre_id)` to check for existing genres before creating new ones — prevents duplicate genre entries.
