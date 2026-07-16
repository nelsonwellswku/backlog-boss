# Refresh Backlog Covers — Technical Implementation Plan

## Goal

When the "Refresh Backlog" button is pressed, enqueue a FastAPI `BackgroundTask` that fetches cover images from IGDB for any games in the user's backlog where `cover_image_id IS NULL`. The refresh response returns immediately; the cover fetch happens asynchronously.

## Current State

- `POST /api/user/refresh-my-backlog` triggers `RefreshMyBacklogHandler.handle()` which syncs new Steam games and returns `{ backlog_id, games_added_count }`.
- `IgdbGame` table has a `cover_image_id` column (`String(100)`, nullable) — `backend/app/database/models.py:88`.
- Existing IGDB queries already request `cover.image_id` but only during the initial game import (`backend/app/infrastructure/igdb_client.py:106,157`).
- Games imported before cover support shipped have `cover_image_id = NULL`.
- `persist_igdb_games.py` stores `cover_image_id` at line 72: `cover_image_id=game.cover.image_id if game.cover else None`.

## Files to Modify/Create

| File | Action |
|------|--------|
| `backend/app/features/user/user_router.py` | Modify — add `BackgroundTasks`, enqueue cover fetch |
| `backend/app/features/user/fetch_missing_covers_task.py` | Create — background task function |
| `backend/app/infrastructure/igdb_client.py` | Modify — add `get_covers_by_game_ids()` method |
| `backend/tests/features/user/test_fetch_missing_covers_task.py` | Create — tests |

## Step-by-Step Instructions

### Step 1 — Add `get_covers_by_game_ids()` to `IgdbClient`

In `backend/app/infrastructure/igdb_client.py`, add a new method to `IgdbClient`:

```python
def get_covers_by_game_ids(self, game_ids: list[int]) -> dict[int, str]:
    if not game_ids:
        return {}

    formatted_ids = self._format_ids(game_ids)
    endpoint = "games"
    limit = 500
    offset = 0
    covers: dict[int, str] = {}

    while True:
        query = f"""
            fields id, cover.image_id;
            where id = ({formatted_ids}) & cover != null;
            offset {offset};
            limit {limit};
        """

        response_bytes = self._api_request(endpoint, query)
        response_json = json.loads(response_bytes)

        if not response_json:
            break

        for game in response_json:
            if game.get("cover") and game["cover"].get("image_id"):
                covers[game["id"]] = game["cover"]["image_id"]

        if len(response_json) < limit:
            break

        offset += limit

    return covers
```

Key details:
- Queries the `games` endpoint (not `external_games`) filtered by IGDB game IDs
- Requests only `id` and `cover.image_id`
- Filters out games where `cover` is null at the query level (`& cover != null`)
- Batches in groups of 500 (IGDB max limit per request)
- Returns a `dict[int, str]` mapping `igdb_game_id → image_id`
- Reuses existing `_format_ids()` and `_api_request()` methods

### Step 2 — Create the background task

Create `backend/app/features/user/fetch_missing_covers_task.py`:

```python
from logging import getLogger

from sqlalchemy import select

from app.database.engine import create_db_session
from app.database.models import BacklogGame, IgdbGame
from app.infrastructure.igdb_client import IgdbClient

logger = getLogger(__name__)


def fetch_missing_covers_task(backlog_id: int) -> None:
    try:
        with create_db_session() as db:
            # 1. Find all games in the backlog that are missing a cover image
            stmt = (
                select(IgdbGame.igdb_game_id)
                .join(BacklogGame)
                .where(BacklogGame.backlog_id == backlog_id)
                .where(IgdbGame.cover_image_id.is_(None))
            )
            game_ids = list(db.scalars(stmt).all())

            if not game_ids:
                logger.info(
                    "No games missing covers in backlog %d", backlog_id
                )
                return

            # 2. Fetch covers from IGDB
            igdb_client = IgdbClient()
            covers = igdb_client.get_covers_by_game_ids(game_ids)

            if not covers:
                logger.info(
                    "IGDB returned no covers for %d games in backlog %d",
                    len(game_ids),
                    backlog_id,
                )
                return

            # 3. Update games with fetched covers
            updated = 0
            for igdb_game_id, image_id in covers.items():
                stmt = (
                    select(IgdbGame)
                    .where(IgdbGame.igdb_game_id == igdb_game_id)
                    .where(IgdbGame.cover_image_id.is_(None))
                )
                game = db.scalars(stmt).one_or_none()
                if game:
                    game.cover_image_id = image_id
                    updated += 1

            db.commit()
            logger.info(
                "Updated covers for %d games in backlog %d",
                updated,
                backlog_id,
            )
    except Exception:
        logger.exception(
            "Failed to fetch missing covers for backlog %d", backlog_id
        )
```

Key details:
- Creates its own DB session via `create_db_session()` (the request session is closed by the time the background task runs)
- Creates its own `IgdbClient()` — FastAPI DI isn't available in background tasks, so it's instantiated directly (the `IGDBWrapper` is created via `get_igdb_wrapper()` which only needs `AppSettings`, resolved from env vars at import time)
- Wraps everything in try/except — logs exception and exits gracefully, never crashes the process
- Only updates games that still have `cover_image_id IS NULL` (defensive against race conditions)
- Logs success with count of updated games

### Step 3 — Modify the router to enqueue the background task

In `backend/app/features/user/user_router.py`:

```python
from fastapi import APIRouter, BackgroundTasks, Depends

from app.features.user.fetch_missing_covers_task import (
    fetch_missing_covers_task,
)
# ... existing imports ...

@user_router.post("/api/user/refresh-my-backlog")
def refresh_my_backlog(
    bg_tasks: BackgroundTasks,
    handler: RefreshMyBacklogHandler = Depends(),
) -> RefreshMyBacklogResponse:
    result = handler.handle()
    bg_tasks.add_task(fetch_missing_covers_task, result.backlog_id)
    return result
```

Key details:
- `BackgroundTasks` is injected by FastAPI
- `fetch_missing_covers_task` is called with `result.backlog_id` (available from the handler's response)
- The response returns immediately; the background task runs after the response is sent
- No changes to `RefreshMyBacklogHandler` — it remains purely synchronous

### Step 4 — Write tests

Create `backend/tests/features/user/test_fetch_missing_covers_task.py`:

```python
import pytest
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from app.database.models import (
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
)
from app.features.user.fetch_missing_covers_task import (
    fetch_missing_covers_task,
)


def _create_backlog_game(
    db_session: Session,
    backlog: Backlog,
    igdb_game_id: int,
    cover_image_id: str | None = None,
) -> BacklogGame:
    game = IgdbGame(
        igdb_game_id=igdb_game_id,
        name=f"Game {igdb_game_id}",
        total_rating=80.0,
        cover_image_id=cover_image_id,
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
```

Test cases:

1. **`test_fetch_missing_covers_updates_games_without_covers`** — Create a backlog with 3 games that have `cover_image_id=None`. Mock `IgdbClient.get_covers_by_game_ids` to return `{1: "co1z2z", 3: "co4abc"}`. Run the task. Assert games 1 and 3 have covers updated; game 2 remains `None`.

2. **`test_fetch_missing_covers_skips_games_with_existing_covers`** — Create a backlog with 2 games that already have covers. Mock IGDB client. Run the task. Assert no IGDB call is made (the query returns no game IDs).

3. **`test_fetch_missing_covers_handles_igdb_failure`** — Create a backlog with games missing covers. Mock IGDB client to raise an exception. Run the task. Assert no crash, logs warning.

4. **`test_fetch_missing_covers_empty_backlog`** — Create an empty backlog. Run the task. Assert no IGDB call is made.

Note: Each test uses the `db_session` fixture (real SQL Server via Testcontainers). The `IgdbClient` is mocked at the class level to avoid real IGDB API calls.

### Step 5 — Verify

```bash
cd backend
uv run ruff check . && uv run ruff format .
uv run pytest -q -k test_fetch_missing_covers
```

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Where to trigger background task | Router function, not handler | Keeps handler synchronous and testable; router is the orchestration layer |
| DB session in background task | `create_db_session()` (standalone) | Request session is closed before background task runs; need own session |
| IGDB client instantiation | `IgdbClient()` directly | FastAPI DI not available in background tasks; `get_igdb_wrapper()` resolves from env vars at import time |
| Error handling | try/except with logging | Background task failures should never affect the user; logs are sufficient for observability |
| Cover fetch scope | All games with `cover_image_id IS NULL` | Simple approach; re-querying IGDB for games without covers is cheap and avoids tracking "attempted" state |
| IGDB query approach | New `get_covers_by_game_ids()` method | Separate from existing `get_games_by_steam_id()` — different endpoint, different fields, different purpose |
| Response model change | None | User doesn't need to know covers are being fetched; no new fields needed |

## Edge Cases

- **Race condition (multiple refreshes)**: The background task only updates games where `cover_image_id IS NULL` at the time of update. Two concurrent tasks will both run, but the second one will find nothing to update.
- **IGDB rate limits**: The background task queries IGDB in batches of 500. For a backlog of 500 games, this is a single request. Rate limits are unlikely to be hit in normal usage.
- **Games with no IGDB cover**: The IGDB query filters `cover != null` at the API level. Games without covers are simply not returned, and their `cover_image_id` stays `NULL`.
- **New games added during refresh**: The background task runs after the sync completes, so it picks up any newly added games that are also missing covers.
- **Backlog deleted during background task**: The `select` query returns no results; the task exits early with a log message.
