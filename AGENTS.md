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
`openapi.json` is gitignored (root `.gitignore`). Regenerating requires dummy env vars for all Settings fields (see Dockerfile for the pattern). The client uses `@hey-api/openapi-ts`; output lands in `frontend/src/client/`. **Do not hand-edit that directory.**

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
- **API models**: snake_case Python, camelCase wire. Inherit `ApiRequestModel` or `ApiResponseModel` from `app/features/api_model.py`. Requests are alias-strict (`validate_by_name=False`).
- **Frontend imports**: use `@bb` alias (maps to `src/`). Reuse React Query hooks + generated SDK; no raw `fetch`.
- **Settings & DB engine cached** via `@lru_cache`. Tests changing env must call `clear_settings_cache()` / `reset_db_engine()`.
- **Required env vars** (copy `backend/.env.sample` to `.env`): `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_DATABASE`, `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, `STEAM_API_KEY`. `dummy_settings` fixture provides defaults for unit tests.
- **`base_url`** controls Steam OpenID return realm; defaults to `http://localhost:5173`.
- **SQL style**: Always use lowercase keywords. Avoid brackets unless required (e.g. when column names are SQL keywords).

## Deploy

GitHub Actions in `.github/workflows/`. Release pipeline: checks → tests → publish image (`ghcr.io`) → run migrations → deploy to Azure App Service (port 9000). OIDC setup: `scripts/setup-azure-github-oidc.sh`.
