# Backlog Boss Copilot Instructions

## Build, test, and lint commands

### Local services

```bash
docker compose up
```

Starts SQL Server plus Grate to create the local `BacklogBoss` database and apply the root-level migrations from `./migrations`.

### Full application image

```bash
docker build -t backlog-boss .
```

This multi-stage build generates `backend/openapi.json`, regenerates the frontend client, builds the frontend, and packages the FastAPI app plus static assets into one image.

### Backend (`/backend`)

```bash
cd backend
uv sync
uv run fastapi dev main.py
```

```bash
cd backend
uv run pytest -q
```

```bash
cd backend
uv run pytest -q tests/features/health/test_get_liveness_handler.py::test_handle_returns_service_up_message
```

```bash
cd backend
uv run ruff check .
uv run ruff format .
```

Backend tests use Testcontainers plus a short-lived Grate container, so Docker must be available locally even when running an individual test.

When creating backend tests, do not mock the SQLAlchemy session or other database connections. Tests that exercise database code should _actually run the database code_.

### Frontend (`/frontend`)

If backend routes or API models change, regenerate the OpenAPI schema and client before working on the frontend:

```bash
cd backend
uv run python export_openapi.py
cd ../frontend
npm run genclient
```

```bash
cd frontend
npm install
npm run dev
```

```bash
cd frontend
npm run build
npm run lint
npm run test -- --run
```

```bash
cd frontend
npm run test -- --run tests/blended-comparator.test.ts
```

## High-level architecture

- The backend is a single FastAPI app in `backend/main.py`. It wires four router groups: health, auth, user, and backlog-game. When `backend/static` exists, the same app also serves the built React SPA and falls back to `index.html` for non-API routes.
- The frontend is a React + Vite SPA in `frontend/src`. During local development, Vite proxies `/api` to `http://localhost:8000`. In production, the Docker build copies `frontend/dist` into the backend image so FastAPI serves both API and UI.
- The API contract flows from backend to frontend. `backend/export_openapi.py` generates `backend/openapi.json`, normalizes operation IDs for nicer SDK names, and `frontend/src/client/**` is regenerated from that schema with `npm run genclient`.
- SQL Server is the only database. Schema migrations live in the repository root under `migrations/`, are applied locally by `docker compose`, in tests by a Grate Testcontainers setup, and in GitHub Actions by `.github/workflows/run-migrations.yml`.
- Backlog creation is a cross-system pipeline: Steam OpenID login creates an app session in SQL Server, `CreateMyBacklogHandler` pulls owned Steam games, `IgdbClient` resolves Steam app IDs to IGDB data, and the backend persists backlog rows only for games that have both rating and time-to-beat data. The frontend `MyBacklog` page then reads and updates that backlog through React Query hooks backed by the generated SDK.

## Key conventions

- Keep backend routes thin. Each feature uses an `APIRouter` plus handler classes that receive dependencies through FastAPI `Depends()` (`DbSession`, `CurrentUser`, `AppSettings`, `SteamClientDep`, `IgdbClientDep`, etc.).
- API models use snake_case in Python and camelCase on the wire. New request/response models should inherit from `ApiRequestModel` or `ApiResponseModel` in `backend/app/features/api_model.py`.
- Request models are alias-strict: clients send camelCase (or explicit aliases such as `openid.ns`), while server code still works with snake_case field names internally.
- Authentication is cookie-based, not token-based. The app uses a `session_key` cookie backed by the `AppSession` table, and `get_current_user()` reads that cookie directly from the request.
- Do not hand-edit `frontend/src/client/**`. It is generated from `backend/openapi.json` and is already excluded from frontend ESLint.
- Frontend imports use the `@bb` alias from `vite.config.ts` / `vitest.config.ts`. Reuse the existing React Query hooks and generated SDK functions instead of adding ad-hoc fetch wrappers.
- Backend settings, DB engine/session factory, and the shared HTTP client are dependency-managed and cached. If tests change environment-driven settings or DB connectivity, clear the settings/engine caches instead of working around stale state.
- SQLAlchemy models map to the `bb` schema. Grate uses the separate `bbgrate` schema for migration bookkeeping, so schema-related changes usually involve both ORM expectations and root migration files.
