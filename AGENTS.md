# Backlog Boss Agent Instructions

## Quick commands

### Backend (`backend/`)
```bash
uv sync                           # install deps
uv run fastapi dev main.py        # dev server on :8000
uv run pytest -q                  # all tests
uv run pytest -q -k test_name     # single test by name
uv run ruff check . && uv run ruff format .  # lint + format
```

Backend tests use Testcontainers (SQL Server + Grate). Docker must be running even for a single test. Do not mock SQLAlchemy — tests exercise real DB code. Each `db_session` fixture wraps a test in a rollback transaction.

### Frontend (`frontend/`)
```bash
npm install          # Node >=24 (see .nvmrc)
npm run dev          # Vite on :5173, proxies /api to :8000
npm run build        # tsc -b && vite build
npm run lint         # ESLint
npm run format       # Prettier
npm run test -- --run                     # all tests once
npm run test -- --run path/to/test.ts     # single test
```

### Codegen (when backend API changes)
```bash
cd backend && uv run python export_openapi.py && cd ../frontend && npm run genclient
```
`openapi.json` is gitignored (root `.gitignore`). The client uses `@hey-api/openapi-ts`; output lands in `frontend/src/client/`. **Do not hand-edit that directory.** Your `.env` already provides all required env vars, so codegen runs without extra setup. In CI/Docker, dummy values are used instead (see `Dockerfile` for the full list of required vars) — the values aren't used, they just satisfy Pydantic settings validation at import time.

### Local DB
```bash
docker compose up
```
SQL Server + Grate, applies `migrations/` to create `BacklogBoss` database.

### Full Docker build
```bash
docker build -t backlog-boss .
```
Multi-stage: generates OpenAPI schema → builds frontend → packages FastAPI + static.

## Architecture

- **Single FastAPI app** (`backend/main.py`) with five routers: `health`, `auth`, `user`, `backlog_game`, `game`. When `backend/static/` exists, serves the React SPA with index.html fallback for non-API routes.
- **React + Vite SPA** (`frontend/src/`). Dev proxies `/api` → `localhost:8000`. Prod copies `frontend/dist` into the backend image.
- **SQL Server only.** ORM schema: `bb`. Grate schema: `bbgrate`. Migrations: `migrations/up/`.
- **Auth**: Cookie-based (`session_key`). `get_current_user()` reads cookie from request, returns `User` dataclass.
- **Backlog pipeline**: Steam OpenID login → session in SQL Server → `CreateMyBacklogHandler` pulls owned Steam games → `IgdbClient` resolves to IGDB data → persists only games with both rating and time-to-beat.

## Key conventions

- **Routes are thin**: handlers receive deps via `Depends()` (`DbSession`, `CurrentUser`, `AppSettings`, `SteamClientDep`, `IgdbClientDep`, `HttpClient`).
- **DI type aliases**: For any class that should be injectable by FastAPI (e.g. a handler or service), define a type alias next to it: `MyClassDep: TypeAlias = Annotated[MyClass, Depends(MyClass)]`. Consumers import `MyClassDep`, never `Depends` directly. This keeps the injection point decoupled from FastAPI.
- **API models**: snake_case Python, camelCase wire. Inherit `ApiRequestModel` or `ApiResponseModel` from `app/features/api_model.py`. Requests are alias-strict (`validate_by_name=False`).
- **Frontend imports**: use `@bb` alias (maps to `src/`). Reuse React Query hooks + generated SDK; no raw `fetch`.
- **Settings & DB engine cached** via `@lru_cache`. Tests changing env must call `clear_settings_cache()` / `reset_db_engine()`.
- **Required env vars** (copy `backend/.env.sample` to `.env`): `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_DATABASE`, `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, `STEAM_API_KEY`. `dummy_settings` fixture provides defaults for unit tests.
- **`base_url`** controls Steam OpenID return realm; defaults to `http://localhost:5173`.
- **SQL style**: Always use lowercase keywords. Avoid brackets unless required (e.g. when column names are SQL keywords).
- **Avoid N+1 queries**: When processing a list of entities, batch-load all required data upfront — use `WHERE ... IN (...)` to fetch parent rows, and `selectinload` / `joinedload` to eager-load relationships. Never call `db.get()`, `db.scalars()`, or access unloaded relationships inside a loop; every iteration produces a separate round trip.
- **No LSP errors**: Even if LSP errors were not introduced by an agent's change, if the agent modifies a file then no LSP errors should remain in that file.
- **Docstrings**: When modifying or creating new functions or methods, always include "Google style" docstrings.

## Database schema context

When working on database-related tasks (new migrations, queries, model changes), load `docs/schema.md` for the current schema reference. Migrations are cumulative and do not represent a "state in time" view — the static schema doc reflects the final state after all migrations are applied.

To regenerate after schema changes:

```bash
cd backend && uv run python ../scripts/generate_schema_docs.py
```

## Deploy

GitHub Actions in `.github/workflows/`. Release pipeline: checks → tests → publish image (`ghcr.io`) → run migrations → deploy to Azure App Service (port 9000). OIDC setup: `scripts/setup-azure-github-oidc.sh`.
