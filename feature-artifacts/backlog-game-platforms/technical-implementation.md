# Backlog Game Platforms — Technical Implementation Plan

## Goal

Add Windows/Mac/Linux platform indicators to the backlog game view and game search results view by fetching platform data from IGDB, persisting it in SQL Server, and displaying brand icons (Windows logo, Apple logo, Tux) after each game's title.

## Current State

- **No platform data exists** anywhere — no DB tables, no ORM models, no API fields, no UI display.
- `IgdbGame` stores `name`, `total_rating`, `cover_image_id` and has relationships to `IgdbExternalGame`, `IgdbGameTimeToBeat`, and `IgdbGenre` (via `IgdbGameGenre`) — `backend/app/database/models.py:80-98`.
- IGDB client (`backend/app/infrastructure/igdb_client.py`) queries `games` and `external_games` endpoints. Fields requested: `game.id, game.name, game.total_rating, game.genres.name, game.cover.image_id`. No platform fields.
- `persist_igdb_games()` (`backend/app/features/game/persist_igdb_games.py`) persists games with genres, external games, and time-to-beat. No platform persistence.
- `BacklogGameRow` API model (`backend/app/features/user/get_my_backlog_handler.py:18-28`) has: `backlog_game_id`, `game_id`, `title`, `total_rating`, `time_to_beat`, `completed_on`, `genres`, `cover_image_id`, `steam_app_id`. No `platform_ids`.
- `GameSearchRow` API model (`backend/app/features/game/search_games_handler.py:14-22`) has: `game_id`, `title`, `total_rating`, `time_to_beat`, `genres`, `cover_image_id`, `steam_app_id`. No `platform_ids`.
- `GetMyBacklogHandler` (`backend/app/features/user/get_my_backlog_handler.py:36-46`) uses `joinedload` for `IgdbGame.time_to_beat`, `IgdbGame.genres`, `IgdbGame.external_games`. No platform load.
- `SearchGamesHandler._load_games_by_ids()` (`backend/app/features/game/search_games_handler.py:83-91`) joins time_to_beat, genres, external_games. No platform load.
- `RefreshMyBacklogHandler` (`backend/app/features/user/refresh_my_backlog_handler.py`) uses `CoverFetcher` and `GenreFetcher` after sync. No platform fetcher.
- `BacklogListItem.tsx` (`frontend/src/pages/my-backlog/BacklogListItem.tsx:51-76`) renders title, Steam link icon, rating, time-to-beat, genres in the primary/secondary slots. No platform icons.
- `GameListItem.tsx` (`frontend/src/pages/games/GameListItem.tsx:56-73`) renders title, Steam link icon, rating chip, time chip, genres. No platform icons.
- Generated client types (`frontend/src/client/types.gen.ts`) have `BacklogGameRow` and `GameSearchRow` without `platformIds`.

## Files to Modify/Create

### Backend

| File | Action |
|------|--------|
| `migrations/up/0011.sql` | Create — `IgdbPlatform` and `IgdbGamePlatform` tables |
| `backend/app/database/models.py` | Modify — add `IgdbPlatform`, `IgdbGamePlatform` ORM models, `platforms` relationship on `IgdbGame` |
| `backend/app/infrastructure/igdb_client.py` | Modify — add `PLATFORM_*` constants, `PlatformResponse`, add `platforms.id` to fields, parse platforms from response |
| `backend/app/features/game/persist_igdb_games.py` | Modify — persist `IgdbGamePlatform` rows alongside genres/external games |
| `backend/app/features/user/platform_fetcher.py` | Create — `PlatformFetcher` class (parallel to `GenreFetcher`) |
| `backend/app/features/user/get_my_backlog_handler.py` | Modify — add `platform_ids` to `BacklogGameRow`, join-load platforms in handler |
| `backend/app/features/game/search_games_handler.py` | Modify — add `platform_ids` to `GameSearchRow`, join-load platforms |
| `backend/app/features/user/refresh_my_backlog_handler.py` | Modify — add `PlatformFetcherDep` and call `fetch_and_persist` after cover/genre fetch |
| `backend/app/features/user/user_router.py` | Modify — add `PlatformFetcherDep` to `RefreshMyBacklogHandler` DI |
| `backend/tests/features/user/test_platform_fetcher.py` | Create — tests for `PlatformFetcher` |
| `backend/tests/features/user/test_get_my_backlog_handler.py` | Modify — add platform assertion to existing tests |
| `backend/tests/features/game/test_search_games_handler.py` | Modify — add platform assertion to existing tests |

### Frontend

| File | Action |
|------|--------|
| `frontend/src/components/PlatformIcons.tsx` | Create — inline SVG platform icon components |
| `frontend/src/pages/my-backlog/BacklogListItem.tsx` | Modify — render `<PlatformIcons>` after title, before Steam link |
| `frontend/src/pages/games/GameListItem.tsx` | Modify — render `<PlatformIcons>` after title, before Steam link |

### Codegen

| Step | Action |
|------|--------|
| `cd backend && uv run python export_openapi.py` | Run — regenerate `openapi.json` |
| `cd frontend && npm run genclient` | Run — regenerate `frontend/src/client/` |

## Step-by-Step Instructions

### Step 1 — Create migration `0011.sql`

Create `migrations/up/0011.sql`:

```sql
create table bb.IgdbPlatform (
    Id int not null,
    Name varchar(32) not null,
    constraint PK_IgdbPlatform primary key (Id)
);

insert into bb.IgdbPlatform (Id, Name) values
    (6, 'Windows'),
    (14, 'Mac'),
    (3, 'Linux');

create table bb.IgdbGamePlatform (
    IgdbGameId int not null,
    IgdbPlatformId int not null,
    constraint PK_IgdbGamePlatform primary key (IgdbGameId, IgdbPlatformId),
    constraint FK_IgdbGamePlatform_IgdbGame foreign key (IgdbGameId) references bb.IgdbGame(Id),
    constraint FK_IgdbGamePlatform_IgdbPlatform foreign key (IgdbPlatformId) references bb.IgdbPlatform(Id)
);
```

### Step 2 — Add ORM models

In `backend/app/database/models.py`, add after `IgdbGameGenre`:

```python
class IgdbPlatform(Base):
    __tablename__ = "IgdbPlatform"
    igdb_platform_id: Mapped[int] = mapped_column(
        "Id", primary_key=True, autoincrement=False
    )
    name: Mapped[str] = mapped_column("Name", String(32))


class IgdbGamePlatform(Base):
    __tablename__ = "IgdbGamePlatform"
    igdb_game_id: Mapped[int] = mapped_column(
        "IgdbGameId", ForeignKey("bb.IgdbGame.Id"), primary_key=True
    )
    igdb_platform_id: Mapped[int] = mapped_column(
        "IgdbPlatformId", ForeignKey("bb.IgdbPlatform.Id"), primary_key=True
    )
```

Add a `platforms` relationship to `IgdbGame`:

```python
class IgdbGame(Base):
    # ... existing columns ...
    platforms: Mapped[list["IgdbPlatform"]] = relationship(
        "IgdbPlatform", secondary="bb.IgdbGamePlatform", lazy="raise"
    )
```

Place it alongside the existing `genres` relationship (after line 98).

### Step 3 — Add platform constants and update IGDB client

In `backend/app/infrastructure/igdb_client.py`, add constants after the imports:

```python
PLATFORM_WINDOWS = 6
PLATFORM_MAC = 14
PLATFORM_LINUX = 3
PLATFORM_IDS = {PLATFORM_WINDOWS, PLATFORM_MAC, PLATFORM_LINUX}
```

Add a response model after `CoverResponse`:

```python
class PlatformResponse(BaseModel):
    id: int
```

Add `platforms` field to `IgdbGameResponse` (line 64, after `cover`):

```python
    platforms: list[PlatformResponse] = Field(default_factory=list)
```

Update the `fields` clause in `get_games_by_steam_id()` (line 134) to include `game.platforms.id`:

```python
query = f"""
    fields game.id, game.name, game.total_rating, game.genres.name, game.cover.image_id, game.platforms.id;
    where uid = ({formatted_steam_ids}) & external_game_source = 1;
    offset {offset};
    limit {limit};
"""
```

Update `search_games_by_name()` (line 185) to include `platforms.id`:

```python
query = f"""
    fields id, name, total_rating, genres.name, cover.image_id, platforms.id;
    search {json.dumps(normalized_name)};
    where external_games != null & external_games.external_game_source = (1);
    limit 50;
"""
```

Add a `get_platforms_by_game_ids()` method to `IgdbClient` (parallel to `get_genres_by_game_ids`):

```python
def get_platforms_by_game_ids(
    self, game_ids: list[int]
) -> dict[int, list[int]]:
    """Fetch platform IDs from IGDB for the given game IDs.

    Args:
        game_ids: IGDB game IDs to fetch platforms for.

    Returns:
        Mapping of game ID to list of platform IDs (only PC platforms: 3, 6, 14).
    """
    if not game_ids:
        return {}

    formatted_ids = self._format_ids(game_ids)
    endpoint = "games"
    limit = 500
    offset = 0
    platforms: dict[int, list[int]] = {}

    while True:
        query = f"""
            fields id, platforms.id;
            where id = ({formatted_ids}) & platforms != null;
            offset {offset};
            limit {limit};
        """

        response_bytes = self._api_request(endpoint, query)
        response_json = json.loads(response_bytes)

        if not response_json:
            break

        for game in response_json:
            game_id = game["id"]
            if "platforms" in game and game["platforms"]:
                pids = [
                    p["id"]
                    for p in game["platforms"]
                    if p["id"] in PLATFORM_IDS
                ]
                if pids:
                    platforms[game_id] = pids

        if len(response_json) < limit:
            break

        offset += limit

    return platforms
```

### Step 4 — Update `persist_igdb_games()`

In `backend/app/features/game/persist_igdb_games.py`, add imports:

```python
from app.database.models import (
    IgdbExternalGame,
    IgdbGame,
    IgdbGamePlatform,
    IgdbGameTimeToBeat,
    IgdbGenre,
    IgdbPlatform,
)
```

At the end of the `for game in games:` loop (before `games_to_add.append(igdb_game)`, after the external games block that ends ~line 101), add platform persistence:

```python
        for platform in game.platforms:
            if platform.id not in PLATFORM_IDS:
                continue
            platform_obj = db.get(IgdbPlatform, platform.id)
            if platform_obj is None:
                platform_obj = IgdbPlatform(igdb_platform_id=platform.id)
                db.add(platform_obj)
            igdb_game.platforms.append(platform_obj)
```

Add the `PLATFORM_IDS` import at the top of the file:

```python
from app.infrastructure.igdb_client import PLATFORM_IDS
```

### Step 5 — Create `PlatformFetcher`

Create `backend/app/features/user/platform_fetcher.py`:

```python
from logging import getLogger
from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.engine import DbSession
from app.database.models import IgdbGame, IgdbGamePlatform, IgdbPlatform
from app.infrastructure.igdb_client import IgdbClientDep

logger = getLogger(__name__)


class PlatformFetcher:
    def __init__(self, db: DbSession, igdb_client: IgdbClientDep):
        self.db = db
        self.igdb_client = igdb_client

    def fetch_and_persist(self, game_ids: list[int]) -> None:
        """Fetch platforms from IGDB for games that are missing them and persist.

        Args:
            game_ids: IGDB game IDs to check and potentially update.
        """
        stmt = select(IgdbGame.igdb_game_id).where(
            IgdbGame.igdb_game_id.in_(game_ids),
            ~select(IgdbGamePlatform.igdb_game_id)
            .where(IgdbGamePlatform.igdb_game_id == IgdbGame.igdb_game_id)
            .exists(),
        )
        missing_ids = list(self.db.scalars(stmt).all())

        if not missing_ids:
            logger.info("No games missing platforms among %d provided", len(game_ids))
            return

        platforms_by_game = self.igdb_client.get_platforms_by_game_ids(missing_ids)

        if not platforms_by_game:
            logger.info("IGDB returned no platforms for %d games", len(missing_ids))
            return

        stmt = (
            select(IgdbGame)
            .where(IgdbGame.igdb_game_id.in_(platforms_by_game.keys()))
            .options(selectinload(IgdbGame.platforms))
        )
        games = {g.igdb_game_id: g for g in self.db.scalars(stmt).all()}

        all_platform_ids = {
            pid for pid_list in platforms_by_game.values() for pid in pid_list
        }
        stmt = select(IgdbPlatform).where(
            IgdbPlatform.igdb_platform_id.in_(all_platform_ids)
        )
        existing_platforms = {
            p.igdb_platform_id: p for p in self.db.scalars(stmt).all()
        }

        for igdb_game_id, pid_list in platforms_by_game.items():
            game = games.get(igdb_game_id)
            if not game:
                continue

            for pid in pid_list:
                platform = existing_platforms.get(pid)
                if not platform:
                    platform = IgdbPlatform(igdb_platform_id=pid)
                    self.db.add(platform)
                    existing_platforms[pid] = platform
                game.platforms.append(platform)

        logger.info("Updated platforms for %d games", len(platforms_by_game))


PlatformFetcherDep: TypeAlias = Annotated[PlatformFetcher, Depends(PlatformFetcher)]
```

### Step 6 — Update `BacklogGameRow` and `GetMyBacklogHandler`

In `backend/app/features/user/get_my_backlog_handler.py`, add `platform_ids` to `BacklogGameRow`:

```python
class BacklogGameRow(ApiResponseModel):
    backlog_game_id: int
    game_id: int
    title: str
    total_rating: float | None
    time_to_beat: int | None
    completed_on: datetime | None
    genres: list[str]
    cover_image_id: str | None = None
    steam_app_id: int | None = None
    platform_ids: list[int] = []
```

In the `handle()` method, add `platform` join loading (alongside the existing `time_to_beat`, `genres`, `external_games` on line 44):

```python
        stmt = (
            select(Backlog)
            .options(
                igdb_game_loader.joinedload(IgdbGame.time_to_beat),
                igdb_game_loader.joinedload(IgdbGame.genres),
                igdb_game_loader.joinedload(IgdbGame.external_games),
                igdb_game_loader.joinedload(IgdbGame.platforms),
            )
            .where(Backlog.app_user_id == self.current_user.app_user_id)
        )
```

In the `BacklogGameRow` constructor (inside the list comprehension, ~line 67), add `platform_ids`:

```python
        backlog_game_rows = [
            BacklogGameRow(
                backlog_game_id=g.backlog_game_id,
                game_id=g.igdb_game_id,
                title=g.igdb_game.name,
                total_rating=g.igdb_game.total_rating,
                time_to_beat=g.igdb_game.time_to_beat.normally
                if g.igdb_game.time_to_beat
                else None,
                completed_on=g.completed_on,
                genres=[genre.name for genre in g.igdb_game.genres],
                cover_image_id=g.igdb_game.cover_image_id,
                steam_app_id=next(
                    (
                        eg.uid
                        for eg in g.igdb_game.external_games
                        if eg.igdb_external_game_source_id == 1
                    ),
                    None,
                ),
                platform_ids=[p.igdb_platform_id for p in g.igdb_game.platforms],
            )
            for g in backlog.backlog_games
        ]
```

### Step 7 — Update `GameSearchRow` and `SearchGamesHandler`

In `backend/app/features/game/search_games_handler.py`, add `platform_ids` to `GameSearchRow`:

```python
class GameSearchRow(ApiResponseModel):
    game_id: int
    title: str
    total_rating: float | None
    time_to_beat: int | None
    genres: list[str]
    cover_image_id: str | None
    steam_app_id: int | None = None
    platform_ids: list[int] = []
```

In `_load_games_by_ids()`, add the `platforms` join:

```python
        stmt = (
            select(IgdbGame)
            .join(IgdbExternalGame)
            .options(
                joinedload(IgdbGame.time_to_beat),
                joinedload(IgdbGame.genres),
                joinedload(IgdbGame.external_games),
                joinedload(IgdbGame.platforms),
            )
            .where(IgdbExternalGame.igdb_external_game_source_id == 1)
            .where(IgdbGame.igdb_game_id.in_(game_ids))
            .distinct()
        )
```

In `_build_game_search_row()`, add `platform_ids`:

```python
    def _build_game_search_row(self, game: IgdbGame) -> GameSearchRow:
        return GameSearchRow(
            game_id=game.igdb_game_id,
            title=game.name,
            total_rating=game.total_rating,
            time_to_beat=game.time_to_beat.normally if game.time_to_beat else None,
            genres=[g.name for g in game.genres],
            cover_image_id=game.cover_image_id,
            steam_app_id=next(
                (
                    eg.uid
                    for eg in game.external_games
                    if eg.igdb_external_game_source_id == 1
                ),
                None,
            ),
            platform_ids=[p.igdb_platform_id for p in game.platforms],
        )
```

### Step 8 — Update `RefreshMyBacklogHandler`

In `backend/app/features/user/refresh_my_backlog_handler.py`, add import:

```python
from app.features.user.platform_fetcher import PlatformFetcherDep
```

Add `platform_fetcher` to the constructor:

```python
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
```

In `handle()`, after `self.genre_fetcher.fetch_and_persist(all_backlog_game_ids)` (line 102), add:

```python
        self.platform_fetcher.fetch_and_persist(all_backlog_game_ids)
```

### Step 9 — Create `PlatformIcons` component

Create `frontend/src/components/PlatformIcons.tsx`:

```tsx
import Box from "@mui/material/Box";
import Tooltip from "@mui/material/Tooltip";

const PLATFORMS = {
  6: { name: "Windows", path: "M0 0h11.6v5.25H6.55v11.55H5.05V5.25H0Z" },
  14: { name: "Mac", path: "M11.6.15c.05 1.3-.4 2.55-1.2 3.5-.75.9-1.95 1.6-3.15 1.5-.2-1.25.35-2.5 1.1-3.4C8.2.9 9.45.25 11.6.15ZM7.45 5.5c1.75.1 3.2 1.05 4.25 2.3-1.65 1-2.5 2.45-2.5 4.15 0 1.95 1.1 3.75 2.9 4.75-.7 1.45-1.9 2.9-3.3 4.15-1.6 1.45-3.15 2.8-5.25 2.8-2.1 0-3.05-1.3-5.2-1.3-2.15 0-3.35 1.25-5.2 1.35-2.05.1-4.05-2.55-5.65-5.25C-2.15 13.75-2.6 8.7 0 5.9 1.45 3.7 3.65 2.35 5.95 2.25c1.9-.15 3.65 1.05 4.65 1.05s3.15-1.3 5.3-.9c.15 0 .25.05.35.1-.45 1.3-1.05 2.5-1.8 3.5v.3c-.05 0-.65.25-1.95.7h-.05Z" },
  3: { name: "Linux", path: "M8.15 0c.15 0 .3.1.35.25l.45 1.6c.25.85.45 1.7.6 2.55.05.2.2.35.4.35h1.95c1.05 0 2.1.4 2.85 1.05.75.65 1.2 1.5 1.2 2.4 0 .75-.3 1.45-.85 2.05-.05.05-.05.15 0 .2.6.55.95 1.3.95 2.1 0 1.05-.55 2.05-1.45 2.7v.3c.05.15.05.3.05.5 0 1.25-.9 2.3-2.4 2.75-.45.15-.95.2-1.45.2H6.8c-.25 0-.45.15-.55.35-.25.65-.55 1.3-.9 1.9-.1.2-.3.35-.55.35s-.45-.15-.55-.35c-.35-.6-.65-1.25-.9-1.9-.1-.2-.3-.35-.55-.35H2.65c-.6 0-1.15-.1-1.6-.3-1.35-.55-2.2-1.6-2.2-2.95 0-.2 0-.4.05-.6.05-.35.15-.65.25-.9.1-.15.1-.3 0-.45-.45-.65-.7-1.4-.7-2.2 0-1.25.55-2.35 1.5-3.15-.05-.05-.05-.1-.05-.15 0-.2.05-.4.15-.55.55-.7.85-1.55.85-2.45 0-.7-.2-1.4-.55-2 0-.05-.05-.1-.05-.15C.95 5.35 1.8 4.1 3.05 3.3c1-.65 2.15-.95 3.4-.95h1.25c.2 0 .35-.15.4-.35.15-.85.35-1.7.6-2.55.05-.15.2-.25.35-.25h1.1zM2.65 7.7c-.15.25-.25.55-.25.8v.35c0 .5.2 1 .45 1.4.1.15.3.2.45.1.15-.1.2-.3.1-.45-.2-.3-.3-.7-.3-1.05v-.35c0-.15-.05-.3-.15-.4-.1-.1-.2-.4-.3-.4h-.05c-.05 0-.05 0-.05.05 0 .05 0 .05.05.1.05.05.05.1.05.15 0 .05 0 .1-.05.15-.05-.05-.1-.1-.1-.1-.05 0-.1.05-.15.1.15-.2.25-.35.35-.55-.05.05-.1.15-.1.25 0 0 0 .05-.05.05h-.05c0-.05.05-.1.05-.15.05-.05.05-.1.1-.15.05-.1.15-.15.2-.2.1-.05.15-.1.2-.1-1.1.25-2.05.75-2.8 1.45-.1.1-.1.25 0 .35.1.1.25.1.35 0 .85-.7 1.9-1.15 3.1-1.3-.05.05-.05.05-.05.1zM3.45 5.85c-.1.15-.15.3-.15.5 0 .35.15.7.35.95.1.15.3.15.45.05.15-.1.15-.3.05-.45-.15-.2-.25-.4-.25-.65 0-.15 0-.25.1-.35.05-.1.1-.2.1-.3 0-.05 0-.1-.05-.15-.05 0-.1-.05-.15-.05-.05 0-.1.05-.15.1-.1.1-.2.2-.25.3-.05.05-.05.05-.05.05zM8.45 6.2c-1.1-.25-2-.5-2.7-.8-.2-.1-.4-.1-.5.05-.1.15-.05.35.1.45.65.25 1.5.5 2.6.7.15.05.3-.05.35-.2.05-.15 0-.25-.15-.3.1.05.2.05.3.1zm-1.15 1.45c0-.05.05-.1.05-.15-.4.15-.7.35-.95.6-.3.25-.55.65-.55 1.05 0 .4.15.7.4.95.1.1.25.1.35 0 .1-.1.1-.25 0-.35-.15-.15-.25-.35-.25-.6 0-.3.15-.55.3-.75.3-.25.6-.45.95-.6.05-.05.1-.1.1-.15zm-.7 4.15c-.1.05-.15.15-.15.25 0 .2.05.35.1.4.05.15.2.2.35.15.15-.05.2-.2.15-.35 0-.05-.05-.15-.05-.2v-.25c0-.15-.15-.25-.25-.2-.05 0-.1 0-.15.2zM3.2 13.25c.1.15.3.15.45 0 .05-.05.1-.15.1-.2.05-.1.05-.2 0-.3v-.15c0-.1.05-.15.1-.2.1-.1.15-.25.15-.4 0-.15-.1-.25-.2-.3-.05-.05-.15 0-.2.05-.05.05-.1.1-.1.2.05.05.1.1.1.2v.05c0 .1-.05.2-.1.25-.1.1-.15.25-.15.4 0 .15.05.25.1.3-.1-.05-.15-.1-.2-.15-.05-.05-.15-.05-.2 0-.05.1-.05.2 0 .25zM5.55 12.4c-.2 0-.4.05-.5.2-.05.05-.05.15-.05.2 0 .15.1.3.25.35.15.05.3 0 .4-.1.05-.05.1-.15.1-.2.05-.1.05-.2 0-.35-.05-.05-.1-.1-.2-.1zm-1.4 1.8c.1.1.25.1.35-.05.05-.1.1-.2.05-.35v-.15c0-.1.05-.15.1-.2.05-.05.1-.1.1-.2 0-.1-.05-.2-.1-.25-.05-.05-.15-.05-.2 0-.05.05-.1.1-.05.2v.05c0 .05-.05.1-.1.15-.1.1-.15.2-.15.35 0 .1.05.25.1.35-.05-.05-.15-.1-.2-.15-.05-.05-.15-.05-.2.05 0 .05 0 .1.05.15.1.05.15.1.2.15zM.85 16.1c.05.2.15.35.3.45.15.1.35.15.6.15.5 0 1.15-.15 1.75-.35 0 .05 0 .1-.05.1.1 0 .2-.05.25-.15.05-.1.05-.2 0-.3-.05-.1-.15-.15-.25-.15-.1 0-.2.05-.25.15v.05c-.05.05-.1.1-.15.1-.1 0-.2.05-.3.05-.1 0-.2 0-.25-.05-.05-.05-.1-.1-.05-.2 0-.1.05-.15.1-.2H4.05c.15 0 .3 0 .45-.05.15-.05.25-.15.25-.3 0-.15-.1-.25-.25-.3-.15-.05-.3-.05-.45-.05H1.35c-.3 0-.5.15-.5.5 0 .35.15.6.5.6.1 0 .25 0 .35-.05-.15.05-.25.1-.35.1-.15 0-.25-.05-.35-.15-.05-.05-.1-.15-.15-.15-.1-.05-.2 0-.25.05-.05.1-.05.2 0 .3zm10.7-9.55c.1.35.15.7.15 1.05 0 .65-.2 1.2-.55 1.7-.05.05-.05.15 0 .2.35.5.55 1.05.55 1.65 0 .8-.35 1.55-.95 2.1.05.05.05.1.05.15 0 1.05-.65 1.9-1.55 2.35.1 1.15.45 1.85 1.05 2.1.55.25 1.15.05 1.6-.25.45-.3.75-.75.8-1.25 0-.05.05-.1.1-.1.1.05.2.15.2.25.05.2.05.4 0 .6-.05.2-.15.4-.3.55-.1.15-.25.25-.4.35-.15.1-.3.15-.35.3-.1.15 0 .35.15.4.15.1.35.05.45-.1.2-.2.35-.4.45-.65.1-.25.15-.5.1-.75.05.05.1.1.15.15.15.15.3.35.4.55.1.2.15.45.1.65-.05.25-.2.45-.4.6-.05.05-.05.15 0 .2.2.2.45.35.75.45.05 0 .1 0 .15-.05.1-.05.15-.15.15-.25 0-.1-.05-.2-.15-.25-.2-.1-.35-.2-.45-.35-.1-.15-.15-.35-.1-.55.05-.15.1-.3.2-.4.15-.2.35-.35.55-.5.2-.15.45-.3.65-.5.2-.2.3-.45.3-.75 0-.3-.1-.6-.25-.85-.1-.15-.05-.35.05-.5.2-.25.35-.55.45-.85.1-.3.1-.65 0-.95-.05-.2-.05-.35 0-.55.05-.2.15-.4.25-.55.15-.2.25-.45.25-.75 0-.45-.15-.9-.4-1.25-.1-.15-.05-.35.05-.5.25-.4.35-.85.35-1.3 0-.85-.35-1.65-.95-2.15-.05-.05-.1-.05-.15-.05-.05 0-.1 0-.15.05-.15.1-.25.25-.3.4-.05.15 0 .35.1.45.2.2.35.4.45.65.1.25.15.5.1.75-.05.2-.15.4-.25.55-.1.15-.15.3-.1.45.05.15.15.3.3.4.2.15.35.35.45.6.1.25.1.55 0 .8-.05.2-.15.35-.3.5-.1.1-.15.25-.1.4.05.15.15.25.3.3.25.15.4.35.5.6.1.25.1.55 0 .8-.1.25-.25.45-.45.6-.15.1-.2.25-.15.4.05.15.15.25.3.3.35.15.55.45.7.75.15.3.2.65.15 1-.05.35-.2.65-.45.9-.15.15-.2.35-.1.5.15.25.25.55.2.85-.05.3-.2.55-.45.75-.15.1-.2.3-.15.45.05.15.15.25.3.3.3.1.5.3.65.55.15.25.2.55.15.85v.2c.1.05.25.05.35.05.06 0 .1-.05.1-.1v-.2c.05-.3 0-.65-.1-.95-.2.2-.35.35-.5.55-.15.2-.25.4-.25.65 0 .25.1.5.3.65.05.05.15.05.2 0 .05-.05.05-.15 0-.2-.15-.1-.2-.25-.2-.45 0-.15.05-.3.15-.4.1-.15.25-.3.4-.4.05 0 .1-.05.15-.1.05-.05.1-.1.1-.15 0-.05 0-.1-.05-.15-.05-.05-.1-.1-.15-.1 0 .05 0 .1-.05.1.05-.05.1-.1.1-.15v-.2c0-.25-.05-.5-.2-.7-.1-.15-.25-.25-.4-.35-.15-.1-.25-.3-.25-.5 0-.2.1-.4.25-.5.2-.15.35-.35.45-.6.1-.25.15-.5.1-.8-.05-.25-.15-.5-.3-.7-.1-.15-.05-.35.05-.5.2-.3.3-.65.3-1 0-.55-.15-1.05-.45-1.45-.1-.15-.1-.35.05-.5.3-.35.45-.8.45-1.25 0-.55-.2-1.05-.55-1.45-.05-.05-.15-.05-.2 0-.05.05-.05.15 0 .2.3.35.45.8.45 1.25 0 .4-.15.75-.35 1.05-.1.15-.1.35 0 .5.25.35.4.8.4 1.25 0 .3-.1.6-.25.85-.1.15-.15.35-.05.5.2.3.35.65.35 1 0 .3-.1.6-.25.85-.1.15-.15.35-.05.5.2.25.3.55.3.85 0 .4-.15.75-.35 1.05-.1.15-.1.35 0 .5.25.35.4.75.4 1.15 0 .45-.15.85-.45 1.15-.1.1-.15.25-.1.4.1.15.15.3.15.5 0 .15 0 .3-.05.4-.05.1-.1.2-.15.25-.05.05-.05.1 0 .15.05.05.1.05.15 0 .1-.1.15-.2.25-.35.05-.15.1-.3.1-.5 0-.2-.05-.4-.15-.55.1-.05.2-.15.25-.25.05-.1.1-.2.1-.35 0-.15-.05-.3-.1-.4.1-.2.15-.45.15-.65 0-.35-.1-.65-.3-.9zm-5.15 4.5c-.35-.15-.7-.25-1.05-.25-.05 0-.1.05-.1.1 0 .05.05.1.1.1.35 0 .7.1 1 .2.05 0 .1 0 .1-.05 0-.05-.05-.1-.05-.1zm6.6-3.25c-.05-.15-.15-.25-.25-.35-.05-.05-.15-.05-.2 0-.05.05-.05.15 0 .2.1.1.15.2.2.35 0 .05.05.1.1.1.05 0 .1-.05.1-.1.05-.05.05-.15.05-.2zM16.9 10.8c-.1 0-.2.05-.2.15 0 .1.05.2.15.2.1 0 .2-.05.2-.15 0-.1-.05-.2-.15-.2z" }
} as const;

type PlatformId = keyof typeof PLATFORMS;

const ICON_SIZE = 18;

function PlatformSvg({ path, label }: { path: string; label: string }) {
  return (
    <svg
      viewBox="0 0 18 18"
      width={ICON_SIZE}
      height={ICON_SIZE}
      aria-label={label}
      fill="currentColor"
    >
      <path d={path} />
    </svg>
  );
}

export function PlatformIcon({ platformId }: { platformId: number }) {
  const platform = PLATFORMS[platformId as PlatformId];
  if (!platform) return null;

  return (
    <Tooltip title={platform.name}>
      <Box
        component="span"
        sx={{
          display: "inline-flex",
          alignItems: "center",
          lineHeight: 0,
          color: "text.secondary",
        }}
      >
        <PlatformSvg path={platform.path} label={platform.name} />
      </Box>
    </Tooltip>
  );
}

export function PlatformIcons({ platformIds }: { platformIds: number[] }) {
  if (!platformIds || platformIds.length === 0) return null;

  return (
    <Box
      component="span"
      sx={{
        display: "inline-flex",
        alignItems: "center",
        gap: 0.25,
        ml: 0.5,
      }}
    >
      {platformIds.map((id) => (
        <PlatformIcon key={id} platformId={id} />
      ))}
    </Box>
  );
}
```

### Step 10 — Update `BacklogListItem.tsx`

In `frontend/src/pages/my-backlog/BacklogListItem.tsx`, add import:

```tsx
import { PlatformIcons } from "@bb/components/PlatformIcons";
```

After the `Typography` element for `game.title` and before the Steam link (`game.steamAppId`), add `<PlatformIcons>`:

```tsx
<Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
  <Typography
    variant="body1"
    sx={{
      fontWeight: 500,
      textDecoration: isCompleted ? "line-through" : "none",
    }}
  >
    {game.title}
  </Typography>
  <PlatformIcons platformIds={game.platformIds} />
  {game.steamAppId && (
    <Tooltip title="Open in Steam">
      <IconButton ...>
        <OpenInNewIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  )}
</Box>
```

### Step 11 — Update `GameListItem.tsx`

In `frontend/src/pages/games/GameListItem.tsx`, add import:

```tsx
import { PlatformIcons } from "@bb/components/PlatformIcons";
```

After the `Typography` element for `game.title` and before the Steam link, add `<PlatformIcons>`:

```tsx
<Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
  <Typography variant="h6">{game.title}</Typography>
  <PlatformIcons platformIds={game.platformIds} />
  {game.steamAppId && (
    <Tooltip title="Open in Steam">
      <IconButton ...>
        <OpenInNewIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  )}
</Box>
```

### Step 12 — Regenerate API client

```bash
cd backend && uv run python export_openapi.py
cd ../frontend && npm run genclient
```

This will regenerate `frontend/src/client/types.gen.ts` and include `platformIds: Array<number>` on both `BacklogGameRow` and `GameSearchRow`.

### Step 13 — Backend lint + test

```bash
cd backend
uv run ruff check . && uv run ruff format .
uv run pytest -q
```

### Step 14 — Frontend lint + build

```bash
cd frontend
npm run lint
npm run build
```

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage approach | Join table (`IgdbPlatform` + `IgdbGamePlatform`) | Consistent with existing genres pattern; flexible for any future platforms |
| Platform scope | Only Windows (6), Mac (14), Linux (3) | IGDB has hundreds of platforms; only these three are relevant for a Steam-centric backlog |
| IGDB field | `platforms.id` only | Known IDs filtered client-side to PLATFORM_IDS set; no need to fetch names since we hardcode them in the seed data |
| API representation | `platform_ids: list[int]` | Frontend maps IDs to icons using constants; no DB join needed at read time |
| Backfill strategy | `PlatformFetcher` (parallel to `GenreFetcher`) | Called during refresh-my-backlog alongside cover/genre fetch; passive fill on any new search/create |
| UI placement | After title, before Steam link icon | Shows platform info before the user clicks through to Steam; keeps it visually grouped with the title |
| Empty state | No icons rendered | Games with no platform data show nothing — no greyed-out placeholders |
| Icon source | Inline SVG paths | No extra dependencies; three simple SVG paths; matches the lightweight approach of the rest of the app |
| Platform persistence timing | At `persist_igdb_games()` time | Same as genres/external games — platforms are stored when the game is first imported from IGDB |

## Edge Cases

- **Game with no platforms in IGDB**: `platforms` field is empty/falsy. The game's `platform_ids` will be an empty list `[]`. No icons render.
- **Game with platforms but none of the PC trio**: IGDB returns platforms like "PlayStation 5", "Xbox". `PLATFORM_IDS` filter removes them; `platform_ids` will be `[]`.
- **Existing games before migration**: Their `IgdbGamePlatform` table is empty. On refresh, `PlatformFetcher` backfills them. On search, newly fetched IGDB data includes platforms via `persist_igdb_games`. Existing games with no refresh/search will show no icons until the user re-searches or refreshes.
- **Race condition on platform backfill**: `PlatformFetcher` only inserts rows into `IgdbGamePlatform` for games that have no existing entries (subquery with `NOT EXISTS`). Safe under concurrent refreshes.
- **Platform IDs outside our set in IGDB response**: Filtered out by the `PLATFORM_IDS` check in both `persist_igdb_games` and `get_platforms_by_game_ids`. No extra DB rows created.
- **IGDB API failure during backfill**: `PlatformFetcher` logs and exits gracefully — no crash, no user-facing error.
- **Backlog refresh with thousands of games**: `get_platforms_by_game_ids` paginates in groups of 500, same as all other IGDB batch methods.
