# Implementation Plan: IGDB Game Covers in Backlog List

## Overview

Add cover art images to the backlog list page. Images come from IGDB's public CDN and are embedded directly in the frontend (no proxy or caching needed).

## Key Design Decisions

1. **Direct embed from IGDB CDN** — IGDB image URLs are public and require no auth. The backend stores only a short `image_id` hash; the frontend constructs the full URL. No backend image proxy or file caching needed.
2. **Cover images only** — No screenshots or artworks. Covers are the most consistent and recognizable image type across games.
3. **`cover_big` size (264x374px)** — Large enough to recognize games, small enough to fit in a list row.
4. **Backlog list only** — The game search page stays text-only for now. Covers can be added to search results later.
5. **Left of text layout** — Cover image as the leading element, text content to the right. Standard media list pattern.
6. **Gray placeholder for missing covers** — A styled `Box` with the game's first letter when no cover exists.
7. **Lazy backfill** — Existing games in the DB get covers only when re-fetched. No migration script to backfill. (A decoupled backfill handler may be added later but is out of scope.)

## How IGDB Images Work

IGDB returns an `image_id` (hash string) for each image. The frontend constructs the URL:

```
https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg
```

Available cover sizes: `cover_small` (90x128), `cover_big` (264x374), `thumb` (90x90).

Images are requested by expanding the `cover` field on the `games` endpoint:
```
fields cover.image_id;
```

The `cover` field is a relation to the `covers` endpoint. When expanded, it returns `{ "image_id": "abc123" }`.

**Important**: IGDB images removed from igdb.com exist for 30 days before CDN removal.

## Implementation Steps

### Step 1: Database Migration

**File**: `migrations/up/0010.sql`

```sql
ALTER TABLE bb.IgdbGame ADD CoverImageId nvarchar(100) NULL;
```

This follows the existing migration pattern (see `migrations/up/0009.sql` for reference). The column is nullable because not all games have covers.

### Step 2: Update ORM Model

**File**: `backend/app/database/models.py`

Add a new field to the `IgdbGame` class (after line 87):

```python
class IgdbGame(Base):
    __tablename__ = "IgdbGame"

    igdb_game_id: Mapped[int] = mapped_column(
        "Id", primary_key=True, autoincrement=False
    )
    name: Mapped[str] = mapped_column("Name", String(255))
    total_rating: Mapped[Optional[float]] = mapped_column("TotalRating")
    cover_image_id: Mapped[Optional[str]] = mapped_column("CoverImageId", String(100))
    # ... rest of relationships unchanged
```

The column name `CoverImageId` matches the SQL migration. `String(100)` is sufficient — IGDB image IDs are ~20 chars.

### Step 3: Update IGDB Client

**File**: `backend/app/infrastructure/igdb_client.py`

#### 3a. Add `CoverResponse` model

Add after the `GenreResponse` class (after line 48):

```python
class CoverResponse(BaseModel):
    image_id: str
```

#### 3b. Add `cover` field to `IgdbGameResponse`

```python
class IgdbGameResponse(BaseModel):
    id: int
    name: str
    total_rating: float | None = None
    genres: list[GenreResponse] = Field(default_factory=list)
    external_games: list["ExternalGameResponse"] = Field(default_factory=list)
    time_to_beat: "TimeToBeatResponse | None" = None
    cover: CoverResponse | None = None
```

#### 3c. Update `get_games_by_steam_id` query

Change line 101 from:
```
fields game.id, game.name, game.total_rating, game.genres.name;
```
to:
```
fields game.id, game.name, game.total_rating, game.genres.name, game.cover.image_id;
```

This requests the cover's `image_id` nested inside the `game` object from the `external_games` endpoint.

#### 3d. Update `search_games_by_name` query

Change line 152 from:
```
fields id, name, total_rating, genres.name;
```
to:
```
fields id, name, total_rating, genres.name, cover.image_id;
```

### Step 4: Update Persist Function

**File**: `backend/app/features/game/persist_igdb_games.py`

In the `persist_igdb_games` function, after the `igdb_game` construction (around line 72), add cover_image_id assignment:

```python
igdb_game = IgdbGame(
    igdb_game_id=game.id,
    name=game.name,
    total_rating=game.total_rating,
    cover_image_id=game.cover.image_id if game.cover else None,
)
```

This is a one-line addition. The `cover` field on `IgdbGameResponse` will be `None` when IGDB has no cover for a game, so the conditional handles that case.

### Step 5: Update API Response Model

**File**: `backend/app/features/user/get_my_backlog_handler.py`

Add `cover_image_id` to `BacklogGameRow`:

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
```

Then update the list comprehension in `GetMyBacklogHandler.handle()` (around line 52) to populate it:

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
    )
    for g in backlog.backlog_games
]
```

### Step 6: Regenerate Frontend Client

Run from the repo root:
```bash
cd backend && uv run python export_openapi.py && cd ../frontend && npm run genclient
```

This regenerates `frontend/src/client/types.gen.ts` and `frontend/src/client/sdk.gen.ts` to include the new `coverImageId` field on `BacklogGameRow`.

### Step 7: Update BacklogListItem Component

**File**: `frontend/src/pages/my-backlog/BacklogList.tsx`

#### 7a. Add import for `GamesIcon`

```tsx
import GamesIcon from "@mui/icons-material/Games";
```

#### 7b. Add cover image URL helper

```tsx
const IGDB_CDN_BASE = "https://images.igdb.com/igdb/image/upload/t_cover_big";

function coverImageUrl(imageId: string): string {
  return `${IGDB_CDN_BASE}/${imageId}.jpg`;
}
```

#### 7c. Add placeholder component

```tsx
function CoverPlaceholder({ title }: { title: string }) {
  return (
    <Box
      sx={{
        width: 88,
        height: 124,
        borderRadius: 1,
        backgroundColor: "grey.200",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <Typography variant="h5" color="text.secondary">
        {title.charAt(0).toUpperCase()}
      </Typography>
    </Box>
  );
}
```

#### 7d. Update BacklogListItem layout

Replace the current return statement (lines 46-155) with a flex layout that puts the cover image left of the text:

```tsx
return (
  <ListItem
    sx={{
      py: 2,
      px: 2,
      opacity: isCompleted ? 0.7 : 1,
      "&:hover": {
        backgroundColor: "action.hover",
      },
    }}
  >
    <Box sx={{ display: "flex", gap: 2, flex: 1, minWidth: 0 }}>
      {/* Cover image */}
      {game.coverImageId ? (
        <Box
          component="img"
          src={coverImageUrl(game.coverImageId)}
          alt={game.title}
          sx={{
            width: 88,
            height: 124,
            objectFit: "cover",
            borderRadius: 1,
            flexShrink: 0,
          }}
        />
      ) : (
        <CoverPlaceholder title={game.title} />
      )}

      {/* Text content */}
      <ListItemText
        primary={game.title}
        secondary={
          <Box
            component="span"
            sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 0.75 }}
          >
            {game.timeToBeat !== null && (
              <Typography
                component="span"
                variant="body2"
                color="text.secondary"
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.5,
                  textDecoration: isCompleted ? "line-through" : "none",
                }}
              >
                ⏱️ {Math.round(game.timeToBeat / 3600)}h
              </Typography>
            )}
            {game.totalRating !== null && (
              <Typography
                component="span"
                variant="body2"
                color="text.secondary"
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.5,
                  textDecoration: isCompleted ? "line-through" : "none",
                }}
              >
                ⭐ {Math.round(game.totalRating)}/100
              </Typography>
            )}
            <GenreChips genres={game.genres} />
            {isCompleted && (
              <Chip
                icon={<CheckCircleIcon />}
                label="Completed"
                size="small"
                color="success"
                variant="outlined"
              />
            )}
          </Box>
        }
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
      />
    </Box>

    {/* Action buttons */}
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, ml: 2 }}>
      <Tooltip
        title={
          isCompleted
            ? "Mark this game as active again"
            : "Mark this game as completed"
        }
      >
        <span>
          <Button
            size="small"
            variant={isCompleted ? "contained" : "outlined"}
            color={isCompleted ? "success" : "inherit"}
            disabled={isUpdating}
            startIcon={
              isCompleted ? <CheckCircleIcon /> : <CheckCircleOutlinedIcon />
            }
            onClick={() => onToggleCompleted(game)}
          >
            {isCompleted ? "Completed" : "Mark complete"}
          </Button>
        </span>
      </Tooltip>
      <Tooltip title="Remove from backlog">
        <span>
          <IconButton
            color="error"
            aria-label="Remove from backlog"
            disabled={isUpdating}
            onClick={() => onRemoveGame(game)}
          >
            <DeleteOutlinedIcon />
          </IconButton>
        </span>
      </Tooltip>
    </Box>
  </ListItem>
);
```

Key layout details:
- Outer `Box` uses `display: flex` with `gap: 2` (16px) between image and text
- Image is fixed at 88x124px (roughly 2:3 aspect ratio matching `cover_big`)
- `flexShrink: 0` prevents image from collapsing
- `flex: 1` on the text `Box` lets it fill remaining space
- `minWidth: 0` prevents text from overflowing the flex container
- Placeholder uses the same dimensions for consistent layout

## Verification

After implementation, verify with:

1. **Backend tests**: `cd backend && uv run pytest -q` — all existing tests should pass. The new column is nullable so existing test fixtures won't break.
2. **Frontend build**: `cd frontend && npm run build` — TypeScript should compile with the new `coverImageId` field.
3. **Frontend lint**: `cd frontend && npm run lint` — no lint errors.
4. **Manual test**: Start dev servers (`uv run fastapi dev main.py` + `npm run dev`), log in, and check that:
   - Games with covers show the image on the left
   - Games without covers show the gray placeholder with first letter
   - The layout doesn't break at different viewport widths
   - Completed games section also shows covers (dimmed at 0.7 opacity)

## File Change Summary

| File | Change Type | Description |
|---|---|---|
| `migrations/up/0010.sql` | New | Add `CoverImageId` column |
| `backend/app/database/models.py` | Edit | Add `cover_image_id` field to `IgdbGame` |
| `backend/app/infrastructure/igdb_client.py` | Edit | Add `CoverResponse`, update 2 queries |
| `backend/app/features/game/persist_igdb_games.py` | Edit | Save `cover_image_id` on new games |
| `backend/app/features/user/get_my_backlog_handler.py` | Edit | Add field to `BacklogGameRow` response |
| `frontend/src/pages/my-backlog/BacklogList.tsx` | Edit | Add cover image display + placeholder |

## Future Work (Out of Scope)

- **Backfill handler**: A decoupled handler to populate `cover_image_id` for existing games that have NULL. Can be added later as a separate feature.
- **Game search page**: Add covers to `GameListItem` using the same pattern.
- **Screenshot/artwork support**: Add additional image types if needed.
- **Image loading optimization**: Add `loading="lazy"`, `srcSet` for retina, or intersection observer for large lists.
