# Steam Store Link — Technical Implementation Plan

## Goal

Add a compact Steam store link icon next to each game's title on the My Backlog and Games search pages so users can jump to the Steam store page in one click.

## Current State

### Backend — API response models lack Steam App ID

- `BacklogGameRow` (`backend/app/features/user/get_my_backlog_handler.py:18-26`) has no `steam_app_id` field
- `GameSearchRow` (`backend/app/features/game/search_games_handler.py:14-20`) has no `steam_app_id` field
- The Steam App ID *does* exist in the DB — `IgdbExternalGame.uid` with `IgdbExternalGame.igdb_external_game_source_id == 1` (1 = Steam). However, neither handler joins this table when building responses.
  - `GetMyBacklogHandler.handle()` joins `BacklogGame → IgdbGame` and eager-loads `time_to_beat` and `genres`, but not `external_games` (line 38-43)
  - `SearchGamesHandler._load_games_by_ids()` joins `IgdbGame → IgdbExternalGame` for the search filter at line 84, but does not eager-load `external_games` as a relationship, and `_build_game_search_row()` (line 94-101) never reads external game data
- Relationship: `IgdbGame.external_games` (`backend/app/database/models.py:90-92`) is a `list[IgdbExternalGame]` with `back_populates="igdb_game"`

### Frontend — no Steam link anywhere

- `BacklogListItem.tsx` renders the title as a plain `ListItemText` string primary (line 49). Right action area has `[Mark complete btn] [🗑️ delete icon]`.
- `GameListItem.tsx` renders the title as `<Typography variant="h6">{game.title}</Typography>` (line 53). Right action area has `[Add to backlog btn]` or `[In backlog chip]`.
- Both components receive typed props (`BacklogGameRow` / `GameSearchRow`) that currently have no `steamAppId` field
- Test mocks (`frontend/tests/backlog-list.test.tsx:19`, `frontend/tests/remove-game-dialog.test.tsx:16`, `frontend/tests/my-backlog.test.tsx:125,156,190,224,254,284`) already include `steamAppId: 1000` — the types need to catch up
- No `OpenInNew` icon usage exists anywhere in the codebase

## Files to Modify/Create

| File | Action |
|------|--------|
| `backend/app/features/user/get_my_backlog_handler.py` | Modify — add `steam_app_id` field, join `IgdbExternalGame` |
| `backend/app/features/game/search_games_handler.py` | Modify — add `steam_app_id` field, join `IgdbExternalGame` |
| `backend/export_openapi.py` | Run — regenerate `openapi.json` |
| `frontend/src/client/` | Regenerate — `npm run genclient` |
| `frontend/src/pages/my-backlog/BacklogListItem.tsx` | Modify — add Steam link icon next to title |
| `frontend/src/pages/games/GameListItem.tsx` | Modify — add Steam link icon next to title |

## Step-by-Step Instructions

### Step 1 — Add `steam_app_id` to `BacklogGameRow` and update `GetMyBacklogHandler`

**File: `backend/app/features/user/get_my_backlog_handler.py`**

a) Add `ImportError` to the imports (so we can raise if no external games found — though we handle gracefully) and add `IgdbExternalGame` to the imports:

```python
from app.database.models import (
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
)
```

b) Add `steam_app_id: int | None = None` to `BacklogGameRow`:

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
```

c) Add `external_games` to the eager-load chain in `handle()`. Add this line after line 43 (`igdb_game_loader.joinedload(IgdbGame.genres)`) — note the trailing comma:

```python
stmt = (
    select(Backlog)
    .options(
        igdb_game_loader.joinedload(IgdbGame.time_to_beat),
        igdb_game_loader.joinedload(IgdbGame.genres),
        igdb_game_loader.joinedload(IgdbGame.external_games),
    )
    .where(Backlog.app_user_id == self.current_user.app_user_id)
)
```

d) In the `BacklogGameRow` constructor call within the list comprehension (lines 53-64), add `steam_app_id`:

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
    )
    for g in backlog.backlog_games
]
```

This uses `next()` with a generator to find the first Steam external game and extract its `uid`, or `None` if no Steam entry exists.

### Step 2 — Add `steam_app_id` to `GameSearchRow` and update `SearchGamesHandler`

**File: `backend/app/features/game/search_games_handler.py`**

a) Add `steam_app_id: int | None = None` to `GameSearchRow`:

```python
class GameSearchRow(ApiResponseModel):
    game_id: int
    title: str
    total_rating: float | None
    time_to_beat: int | None
    genres: list[str]
    cover_image_id: str | None
    steam_app_id: int | None = None
```

b) In `_load_games_by_ids`, add `joinedload(IgdbGame.external_games)` to the options (line 85):

```python
stmt = (
    select(IgdbGame)
    .join(IgdbExternalGame)
    .options(
        joinedload(IgdbGame.time_to_beat),
        joinedload(IgdbGame.genres),
        joinedload(IgdbGame.external_games),
    )
    .where(IgdbExternalGame.igdb_external_game_source_id == 1)
    .where(IgdbGame.igdb_game_id.in_(game_ids))
    .distinct()
)
```

c) In `_build_game_search_row` (line 94), add `steam_app_id`:

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
    )
```

### Step 3 — Export OpenAPI schema and regenerate frontend client

```bash
cd backend && uv run python export_openapi.py && cd ../frontend && npm run genclient
```

This generates `backend/openapi.json` (gitignored) and regenerates `frontend/src/client/` (types.gen.ts + sdk.gen.ts). The new `steamAppId` field will now appear in `BacklogGameRow` and `GameSearchRow` types.

### Step 4 — Add Steam link to `BacklogListItem.tsx`

**File: `frontend/src/pages/my-backlog/BacklogListItem.tsx`**

a) Add the icon import at the top:

```typescript
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
```

(`IconButton`, `Tooltip`, `Box`, `Typography` are already imported.)

b) Change the title from a plain string to a `Box` containing the title text + optional Steam icon. Replace:

```tsx
<ListItemText
  primary={game.title}
  slotProps={{
    primary: {
      variant: "body1",
      sx: {
        fontWeight: 500,
        textDecoration: isCompleted ? "line-through" : "none",
      },
    },
    secondary: {
      component: "div",
    },
  }}
  // ... secondary ...
/>
```

With:

```tsx
<ListItemText
  primary={
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
      {game.steamAppId && (
        <Tooltip title="Open in Steam">
          <IconButton
            size="small"
            component="a"
            href={`https://store.steampowered.com/app/${game.steamAppId}`}
            target="_blank"
            rel="noopener noreferrer"
            sx={{ p: 0.5 }}
          >
            <OpenInNewIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  }
  slotProps={{
    secondary: {
      component: "div",
    },
  }}
  // ... secondary as before ...
/>
```

Note: `slotProps.primary` is removed — styling is now applied directly to the inner `Typography`.

### Step 5 — Add Steam link to `GameListItem.tsx`

**File: `frontend/src/pages/games/GameListItem.tsx`**

a) Add the icon and MUI imports at the top:

```typescript
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
```

(`Box` is already imported at line 5; add the other three.)

b) Change the title area from a single `Typography` to a `Box` with the title + optional Steam icon. Replace:

```tsx
<Typography variant="h6">{game.title}</Typography>
```

With:

```tsx
<Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
  <Typography variant="h6">{game.title}</Typography>
  {game.steamAppId && (
    <Tooltip title="Open in Steam">
      <IconButton
        size="small"
        component="a"
        href={`https://store.steampowered.com/app/${game.steamAppId}`}
        target="_blank"
        rel="noopener noreferrer"
        sx={{ p: 0.5 }}
      >
        <OpenInNewIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  )}
</Box>
```

The title is inside a `Stack` within `ListItemText` primary, so the `Box` fits naturally there.

### Step 6 — Verify

```bash
cd backend && uv run ruff check . && uv run ruff format .
cd ../frontend && npm run lint && npm run format
cd ../backend && uv run pytest -q
cd ../frontend && npm run test -- --run
```

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Where to get `steam_app_id` | From `IgdbExternalGame.uid` via eager-load | Data already exists in DB; no new queries or API calls needed |
| How to extract `steam_app_id` | `next()` generator expression with `igdb_external_game_source_id == 1` filter | Simple, no new helper needed; gracefully returns `None` if no Steam entry |
| Frontend URL construction | `https://store.steampowered.com/app/${steamAppId}` | Steam store URL format is stable and well-known; no need for backend to store full URL |
| Link element | MUI `IconButton` with `component="a"` | Consistent with existing delete `IconButton` pattern; renders as a native `<a>` for accessibility |
| Icon | `OpenInNewIcon` from MUI | No external assets needed; universally recognized "external link" meaning |
| Placement | Next to title in the primary text slot | Compact; keeps the right-side action area free for primary actions (mark complete, add to backlog) |
| New tab | `target="_blank" rel="noopener noreferrer"` | Standard security practice for external links |
| Conditional render | Only when `steamAppId` is non-null | Some games may not have a Steam App ID; no broken or empty link |
| Background task for stale data | Not implemented | The `steam_app_id` is persisted at game-import time and is stable; a refresh-backlog flow already re-imports games if needed |

## Edge Cases

- **Game has no Steam App ID**: The field is `None`. The frontend checks `game.steamAppId` and renders nothing. No broken link is shown.
- **Game has multiple external entries (e.g., Steam + GOG)**: The `next()` generator picks the first Steam entry (`source_id == 1`). Each Steam game should have only one Steam entry, so this is safe.
- **Backlog game where Steam data was never imported**: A freshly added game (via "Add to backlog" from search) already goes through `persist_igdb_games` which saves `IgdbExternalGame` rows. If IGDB returned no Steam external game for that title, `steam_app_id` will be `None`.
- **Large backlog (hundreds of games)**: The `external_games` relationship is eager-loaded in a single query via `joinedload`. For the backlog page, there's one query for the backlog + one for the external games (via the join). No N+1 risk.
- **Tests already include steamAppId**: The test mocks in `backlog-list.test.tsx`, `remove-game-dialog.test.tsx`, and `my-backlog.test.tsx` already pass `steamAppId: 1000`. After client regeneration, the `BacklogGameRow` type will include the field, so no test changes are needed.
