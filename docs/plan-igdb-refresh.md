# Plan: IGDB Game Refresh + Permission System

## Overview

Add the ability to refresh IGDB game data (ratings, covers, time-to-beat, genres, platforms) on demand. This requires a permission system to gate admin endpoints, and a background task that batches through stale games and fetches fresh data from IGDB.

---

## Part 1: Permission System

### New Files

1. **`backend/app/auth/__init__.py`** — empty
2. **`backend/app/auth/permissions.py`** — constants for `Permission` and `Resource`
3. **`backend/app/auth/roles.py`** — `ROLES` dict mapping role names to permissions
4. **`backend/app/auth/dependencies.py`** — `requires_authorization(permission, resource)` as a FastAPI `Depends()` factory

### Design

```python
# permissions.py
class Permission:
    READ = "read"
    WRITE = "write"

class Resource:
    IGDB_GAMES = "igdb_games"

# roles.py
ROLES: dict[str, dict[str, list[str]]] = {
    "admin": {
        Resource.IGDB_GAMES: [Permission.READ, Permission.WRITE],
    },
    "user": {},
}

# dependencies.py
def requires_authorization(permission: str, resource: str):
    async def _check(current_user: RequiredCurrentUser, db: DbSession) -> User:
        stmt = select(AppUserRole.role).where(
            AppUserRole.app_user_id == current_user.app_user_id
        )
        roles = set(db.scalars(stmt).all())
        for role in roles:
            role_perms = ROLES.get(role, {}).get(resource, [])
            if permission in role_perms:
                return current_user
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return Depends(_check)
```

### DB Changes

- New table `AppUserRole`:
  - `AppUserId` INT NOT NULL, FK → AppUser.AppUserId
  - `Role` VARCHAR(50) NOT NULL
  - Composite PK: `(AppUserId, Role)`
- New ORM model `AppUserRole` in `models.py`
- Migration `0015.sql`: create table + seed admin for PersonaName = 'Revenant'

---

## Part 2: IGDB Game Refresh

### New Files

1. **`backend/app/features/admin/__init__.py`** — empty
2. **`backend/app/features/admin/admin_router.py`** — `POST /api/admin/refresh-igdb-games`
3. **`backend/app/features/admin/refresh_igdb_games_handler.py`** — endpoint handler, starts background task
4. **`backend/app/features/admin/refresh_igdb_games_job.py`** — background task class
5. **`backend/app/features/admin/update_igdb_games_handler.py`** — updates IgdbGame + related tables

### Endpoint

- Path: `POST /api/admin/refresh-igdb-games`
- Protected by: `requires_authorization(Permission.WRITE, Resource.IGDB_GAMES)`
- Response: `202 Accepted` with `{"status": "started"}`

### Background Task Flow (`RefreshIgdbGamesJob.run()`)

1. Create own `IgdbClient` via `IgdbClient.create()`
2. Create own DB session via `create_db_session()`
3. Try to acquire lock:
   - If lock exists and `LastUpdatedOn` is < 5 min ago → skip (return early)
   - If lock exists and stale (> 5 min) → take over (UPDATE)
   - If no lock → INSERT new lock
4. Query `IgdbGame` where `LastRefreshedAt IS NULL OR LastUpdatedOn < DATEADD(DAY, -30, GETUTCDATE())`
5. Process in batches of 500:
   - Fetch from IGDB (compose existing methods: `get_covers_by_game_ids`, `get_genres_by_game_ids`, `get_platforms_by_game_ids`, `get_game_time_to_beats`)
   - BEGIN TRANSACTION
   - Call `UpdateIgdbGamesHandler` to update all tables
   - UPDATE `IgdbRefreshLock.LastUpdatedOn`
   - COMMIT TRANSACTION
   - Sleep 1 second between batches
6. On completion or error → DELETE lock row

### `UpdateIgdbGamesHandler` Updates Per Game

| Table | Columns Updated | Strategy |
|-------|----------------|----------|
| `IgdbGame` | Name, TotalRating, CoverImageId, LastRefreshedAt | UPDATE existing row |
| `IgdbGameTimeToBeat` | Normally | UPDATE or INSERT if missing |
| `IgdbExternalGame` | Year | UPDATE or INSERT if missing |
| `IgdbGameGenre` | — | DELETE all, INSERT new set |
| `IgdbGamePlatform` | — | DELETE all, INSERT new set |
| `IgdbGenre` | Name | INSERT if new genre doesn't exist |
| `IgdbPlatform` | — | INSERT if new platform doesn't exist |

Games with no IGDB data returned → skip (leave untouched)

---

## Part 3: DB Migrations

### `0015.sql`

```sql
-- Add LastRefreshedAt to IgdbGame
ALTER TABLE bb.IgdbGame ADD LastRefreshedAt datetimeoffset null;
UPDATE bb.IgdbGame SET LastRefreshedAt = '2000-01-01 00:00:00 +00:00';
ALTER TABLE bb.IgdbGame ALTER COLUMN LastRefreshedAt datetimeoffset not null;

-- Create AppUserRole table
CREATE TABLE bb.AppUserRole (
    AppUserId int not null,
    Role varchar(50) not null,
    CONSTRAINT PK_AppUserRole PRIMARY KEY (AppUserId, Role),
    CONSTRAINT FK_AppUserRole_AppUser FOREIGN KEY (AppUserId) REFERENCES bb.AppUser(AppUserId)
);

-- Assign admin role to Revenant
INSERT INTO bb.AppUserRole (AppUserId, Role)
SELECT AppUserId, 'admin' FROM bb.AppUser WHERE PersonaName = 'Revenant';

-- Create IgdbRefreshLock table
CREATE TABLE bb.IgdbRefreshLock (
    LockId varchar(50) not null PRIMARY KEY,
    StartedOn datetimeoffset not null,
    LastUpdatedOn datetimeoffset not null,
    AppUserId int not null,
    CONSTRAINT FK_IgdbRefreshLock_AppUser FOREIGN KEY (AppUserId) REFERENCES bb.AppUser(AppUserId)
);
```

---

## Part 4: Register Router

Add to `backend/main.py`:

```python
from app.features.admin.admin_router import admin_router
app.include_router(admin_router)
```

---

## Part 5: Update `persist_igdb_games`

Modify `backend/app/features/game/persist_igdb_games.py` to set `LastRefreshedAt = now()` on initial insert of new games.

---

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth approach | Permission/Resource/Role system | Extensible, explicit |
| Admin endpoint path | `/api/admin/` prefix | Distinguishes from user endpoints |
| Role storage | DB table (AppUserRole) | Users can have multiple roles |
| Role definitions | Code file (ROLES dict) | No need for DB flexibility |
| First admin | Migration seed (PersonaName = 'Revenant') | Repeatable, version-controlled |
| Permission check | Query DB per request | Role changes take effect immediately |
| Batch size | 500 | Max IGDB allows per request |
| Delay between batches | 1 second | ~3 API calls/batch, under rate limit |
| Lock mechanism | DB row with LastUpdatedOn in transaction | Atomic with game updates |
| Stale lock threshold | 5 minutes | No operation should take that long |
| Lock on completion | DELETE row | Simple, stale timeout handles edge cases |
| Skip if running | Yes | Avoid concurrent task conflicts |
| IGDB client in background task | `IgdbClient.create()` (bypasses DI) | Avoids lifetime management issues |
| Game data not found | Skip (leave untouched) | IGDB might temporarily not return data |
| Genre/platform update | Replace all associations | IGDB is source of truth |
| Endpoint response | 202 Accepted with `{"status": "started"}` | Simple feedback |
| Error handling | Abort entire task, release lock | Something is wrong, user can re-kick |
| New function vs modify | New `UpdateIgdbGamesHandler` class | Clean separation of concerns |
| `LastRefreshedAt` on insert | Set to now on new games | 30-day clock starts when added |
| Existing games `LastRefreshedAt` | Set to '2000-01-01' in migration | Forces refresh on first run |

---

## File Changes Summary

### New Files
- `backend/app/auth/__init__.py`
- `backend/app/auth/permissions.py`
- `backend/app/auth/roles.py`
- `backend/app/auth/dependencies.py`
- `backend/app/features/admin/__init__.py`
- `backend/app/features/admin/admin_router.py`
- `backend/app/features/admin/refresh_igdb_games_handler.py`
- `backend/app/features/admin/refresh_igdb_games_job.py`
- `backend/app/features/admin/update_igdb_games_handler.py`
- `migrations/up/0015.sql`

### Modified Files
- `backend/app/database/models.py` — add `AppUserRole`, `IgdbRefreshLock`, `LastRefreshedAt` on `IgdbGame`
- `backend/app/features/game/persist_igdb_games.py` — set `LastRefreshedAt` on insert
- `backend/main.py` — register admin router
