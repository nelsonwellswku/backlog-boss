# Video Game Genres — Technical Implementation Plan

## Goal

Add genre display to games in search results and backlog views by fetching genre data from IGDB at import time, persisting it in a normalized schema, and exposing it through the API response models.

## Files to Modify

| File | Change |
|---|---|
| `backend/app/database/models.py` | Add `IgdbGenre`, `IgdbGameGenre` models; add `genres` relationship on `IgdbGame` |
| `migrations/up/0009.sql` | Create `bb.IgdbGenre` and `bb.IgdbGameGenre` tables |
| `backend/app/infrastructure/igdb_client.py` | Add `GenreResponse` model; add `genres.name` to IGDB query fields; add `genres` field to `IgdbGameResponse` |
| `backend/app/features/game/persist_igdb_games.py` | Persist `IgdbGenre` rows and junction records alongside new games |
| `backend/app/features/game/search_games_handler.py` | Add `joinedload(IgdbGame.genres)`; include `genres` in `GameSearchRow` |
| `backend/app/features/user/get_my_backlog_handler.py` | Add `joinedload(IgdbGame.genres)`; include `genres` in `BacklogGameRow` |
| `frontend/src/pages/games/GameListItem.tsx` | Display genre chips in the secondary metadata area |
| `frontend/src/pages/my-backlog/BacklogList.tsx` | Display genre chips in the secondary metadata area |

## Step-by-Step Instructions

### Step 1 — Database migration

Create `migrations/up/0009.sql`:

```sql
CREATE TABLE bb.IgdbGenre (
    Id          INT           NOT NULL PRIMARY KEY,
    Name        VARCHAR(100)  NOT NULL
);

CREATE TABLE bb.IgdbGameGenre (
    IgdbGameId  INT NOT NULL REFERENCES bb.IgdbGame(Id),
    IgdbGenreId INT NOT NULL REFERENCES bb.IgdbGenre(Id),
    PRIMARY KEY (IgdbGameId, IgdbGenreId)
);
```

### Step 2 — SQLAlchemy models

In `backend/app/database/models.py`, add three classes:

```python
class IgdbGenre(Base):
    __tablename__ = "IgdbGenre"
    igdb_genre_id: Mapped[int] = mapped_column("Id", primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column("Name", String(100))


class IgdbGameGenre(Base):
    __tablename__ = "IgdbGameGenre"
    igdb_game_id: Mapped[int] = mapped_column("IgdbGameId", ForeignKey("bb.IgdbGame.Id"), primary_key=True)
    igdb_genre_id: Mapped[int] = mapped_column("IgdbGenreId", ForeignKey("bb.IgdbGenre.Id"), primary_key=True)
```

Add to the existing `IgdbGame` class:

```python
class IgdbGame(Base):
    # ... existing columns ...
    genres: Mapped[list[IgdbGenre]] = relationship(
        "IgdbGenre", secondary="bb.IgdbGameGenre", lazy="raise"
    )
```

### Step 3 — IGDB client response models

In `backend/app/infrastructure/igdb_client.py`, add before `IgdbGameResponse`:

```python
class GenreResponse(BaseModel):
    id: int
    name: str
```

Add `genres` field to `IgdbGameResponse`:

```python
class IgdbGameResponse(BaseModel):
    id: int
    name: str
    total_rating: float | None = None
    genres: list[GenreResponse] = Field(default_factory=list)
    external_games: list["ExternalGameResponse"] = Field(default_factory=list)
    time_to_beat: "TimeToBeatResponse | None" = None
```

### Step 4 — IGDB query fields

In `get_games_by_steam_id` (line 95), change:
```
fields game.id, game.name, game.total_rating;
```
to:
```
fields game.id, game.name, game.total_rating, game.genres.name;
```

In `search_games_by_name` (line 146), change:
```
fields id, name, total_rating;
```
to:
```
fields id, name, total_rating, genres.name;
```

### Step 5 — Persist genres

In `persist_igdb_games.py`, add the `IgdbGenre` import to the existing import line:

```python
from app.database.models import IgdbExternalGame, IgdbGame, IgdbGameGenre, IgdbGameTimeToBeat, IgdbGenre
```

At the top of the function body, after the `games_to_add` list is initialized, build a genre cache:

```python
    all_genre_ids: set[int] = set()
    for game in games:
        for g in game.genres:
            all_genre_ids.add(g.id)

    existing_genre_ids = set(
        db.scalars(
            select(IgdbGenre.igdb_genre_id).where(IgdbGenre.igdb_genre_id.in_(all_genre_ids))
        ).all()
    )

    genre_cache: dict[int, IgdbGenre] = {}
    for genre_id in all_genre_ids:
        if genre_id in existing_genre_ids:
            genre_cache[genre_id] = db.get(IgdbGenre, genre_id)
```

Inside the loop that creates each new `IgdbGame` (after the `igdb_game` object is constructed), attach genres:

```python
        for genre in game.genres:
            if genre.id not in genre_cache:
                genre_obj = IgdbGenre(igdb_genre_id=genre.id, name=genre.name)
                db.add(genre_obj)
                genre_cache[genre.id] = genre_obj
            igdb_game.genres.append(genre_cache[genre.id])
```

This code runs before `db.flush()` and works within the same transaction.

### Step 6 — API response models

In `search_games_handler.py`, add `genres` to `GameSearchRow`:

```python
class GameSearchRow(ApiResponseModel):
    game_id: int
    title: str
    total_rating: float | None
    time_to_beat: int | None
    genres: list[str]
```

In `get_my_backlog_handler.py`, add `genres` to `BacklogGameRow`:

```python
class BacklogGameRow(ApiResponseModel):
    backlog_game_id: int
    game_id: int
    title: str
    total_rating: float | None
    time_to_beat: int | None
    completed_on: datetime | None
    genres: list[str]
```

### Step 7 — Add `joinedload` to queries

In `search_games_handler.py`, `_load_games_by_ids`, add `.joinedload(IgdbGame.genres)` to the options:

```python
stmt = (
    select(IgdbGame)
    .join(IgdbExternalGame)
    .options(joinedload(IgdbGame.time_to_beat), joinedload(IgdbGame.genres))
    .where(IgdbExternalGame.igdb_external_game_source_id == 1)
    .where(IgdbGame.igdb_game_id.in_(game_ids))
    .distinct()
)
```

In `get_my_backlog_handler.py`, add `.joinedload(IgdbGame.genres)` to the end of the joinedload chain:

```python
stmt = (
    select(Backlog)
    .options(
        joinedload(Backlog.backlog_games.and_(BacklogGame.removed_on.is_(None)))
        .joinedload(BacklogGame.igdb_game)
        .joinedload(IgdbGame.time_to_beat)
        .joinedload(IgdbGame.genres)
    )
    .where(Backlog.app_user_id == self.current_user.app_user_id)
)
```

### Step 8 — Build rows with genres

In `search_games_handler.py`, `_build_game_search_row`:

```python
return GameSearchRow(
    game_id=game.igdb_game_id,
    title=game.name,
    total_rating=game.total_rating,
    time_to_beat=game.time_to_beat.normally if game.time_to_beat else None,
    genres=[g.name for g in game.genres],
)
```

In `get_my_backlog_handler.py`, the backlog-game row builder:

```python
BacklogGameRow(
    backlog_game_id=g.backlog_game_id,
    game_id=g.igdb_game_id,
    title=g.igdb_game.name,
    total_rating=g.igdb_game.total_rating,
    time_to_beat=g.igdb_game.time_to_beat.normally if g.igdb_game.time_to_beat else None,
    completed_on=g.completed_on,
    genres=[g.name for g in g.igdb_game.genres],
)
```

### Step 9 — Regenerate frontend client

```bash
cd backend && uv run python export_openapi.py && cd ../frontend && npm run genclient
```

This updates `frontend/src/client/types.gen.ts` so `GameSearchRow` and `BacklogGameRow` include `genres: string[]`.

### Step 10 — Frontend: GameListItem.tsx

Import `LocalOfferIcon` (or use a generic label icon) for genre chips. Add genre chips to the secondary `Stack` alongside the existing rating and time-to-beat chips:

```tsx
{game.genres.length > 0 && (
  <>
    {game.genres.slice(0, 3).map((genre) => (
      <Chip key={genre} size="small" label={genre} variant="outlined" />
    ))}
    {game.genres.length > 3 && (
      <Chip size="small" label={`+${game.genres.length - 3}`} variant="outlined" />
    )}
  </>
)}
```

### Step 11 — Frontend: BacklogList.tsx

In the `BacklogListItem` component, add genre chips after the existing `Box` containing time-to-beat and rating. Use the same chip pattern as Step 10 but adapted for the inline layout:

```tsx
{game.genres.length > 0 && (
  <>
    {game.genres.slice(0, 3).map((genre) => (
      <Chip key={genre} size="small" label={genre} variant="outlined" />
    ))}
    {game.genres.length > 3 && (
      <Chip size="small" label={`+${game.genres.length - 3}`} variant="outlined" />
    )}
  </>
)}
```

### Step 12 — Verify

```bash
cd backend && uv run ruff check . && uv run ruff format .
cd frontend && npm run lint && npm run build
```

## Edge Cases and Notes

- **Empty genres**: If `game.genres` is empty (pre-existing game), the frontend renders no chip — no empty string, no placeholder.
- **Multiple genres**: Limit to 3 visible chips with "+N" overflow.
- **Genre name changes in IGDB**: Not handled. Genre names are captured at import time and never updated. IGDB genre names are highly stable.
- **Duplicate genre IDs across games**: The `genre_cache` dict ensures a single `IgdbGenre` row per IGDB genre ID.
- **Test fixtures**: If a test constructs `GameSearchRow` or `BacklogGameRow` directly, it will need `genres=[]` passed explicitly (required field).
