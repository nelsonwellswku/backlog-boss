# Azure App Insights Tracing & Logs via OpenTelemetry — Technical Implementation Plan

## Goal

Ship OpenTelemetry traces and correlated logs to Azure Application Insights via the `azure-monitor-opentelemetry` distro — opt-in through `APPLICATIONINSIGHTS_CONNECTION_STRING`, fail-soft when unset, with credential-bearing URL query params redacted from exported spans.

## Acceptance Criteria (from issue #81)

- No connection string → app starts, console logs unchanged, no telemetry warnings/errors, full test suite passes without Azure credentials.
- With connection string → an HTTP request produces one trace: server span + child spans for outgoing httpx/requests calls and SQLAlchemy queries under one trace ID.
- Existing `logger.*` calls appear in App Insights carrying the trace ID of the request/job that produced them.
- Background job runs (`RefreshIgdbGamesJob`) produce their own traces with identifiable job names.
- No credential data exported: Steam API keys (`key`/`apikey`/`access_token`/`token` query params) redacted from URL span attributes; headers, bodies, SQL bound params, session cookies, Steam client secrets never captured.
- User identifiers present as span attributes: `user.id`, `user.steam_id`.
- Telemetry failures never affect requests; invalid connection string disables export at startup without crashing.
- Shutdown flushes within a bounded timeout (~5s), never hangs.
- Local console logging unchanged with or without telemetry.
- Trace sampling defaults to 100%, tunable purely via env vars with no code change.
- Readiness endpoint reports `telemetry: "enabled" | "disabled"` (readiness only — liveness untouched).
- Deploy workflow syncs the connection string; `.env.sample` documents it; no settings/migration/frontend changes.

## Current State

- `backend/main.py:16` — `logging.basicConfig(level=logging.INFO)`; `main.py:18-25` — app created **at import time** with `lifespan=configure_httpx_lifespan`. No middleware anywhere; no OTel code exists in the backend.
- **Timing constraint**: `FastAPIInstrumentor._instrument()` replaces the `fastapi.FastAPI` class so only apps instantiated *after* instrumentation are traced. Our app predates lifespan, so it needs a manual `FastAPIInstrumentor().instrument_app(app)` call after configure.
- `backend/app/settings.py` — pydantic-settings, `@lru_cache get_settings()`, `clear_settings_cache()`. All fields required except `db_port`, `base_url` (non-empty defaults). An empty-string default is safe and required (a required field would break `export_openapi.py`, Dockerfile dummy envs at `Dockerfile:29-35`, `tests/conftest.py`, and the workflow validate block).
- `backend/app/database/engine.py:29-31` — `@lru_cache get_db_engine()`; `reset_db_engine()` (line 39) used by tests. `create_db_session()` (line 50) is how the background job opens its own session.
- `backend/app/http_client.py:9` — `logging.getLogger("httpx").disabled = True` (secret-leak guard — stays as-is); `configure_httpx_lifespan` (line 12) creates the shared sync `httpx.Client`.
- Health: `get_readiness_handler.py` returns `GetReadinessResponse(message=...)`; liveness stays untouched (decision: readiness only).
- `backend/app/features/admin/refresh_igdb_games_job.py:28` — `RefreshIgdbGamesJob.run(app_user_id)`; body: create client → `create_db_session()` → lock/stale-check/batch loop → release. Triggered via Starlette `BackgroundTasks` from `refresh_igdb_games_handler.py:28`.
- Fetchers: `cover_fetcher.py` / `genre_fetcher.py` / `platform_fetcher.py` each expose `fetch_and_persist(game_ids)` and run **in-request** via `DbSession` DI (injected into `RefreshMyBacklogHandler`).
- `backend/app/features/auth/get_current_user.py:21-46` — resolves `User(app_user_id, steam_id, ...)`; `require_current_user` wraps it.
- Deploy workflow `.github/workflows/deploy-to-azure-app-service.yml` — required vars at lines 67-80; optional-var precedent is `DB_PORT`/`BASE_URL`: step `env` (185/188), append-if-nonempty (204-210), delete-if-empty (219-235).
- Tests: only `tests/features/admin/test_admin_router.py` boots the app (`TestClient(app)` runs the lifespan). Job tests monkeypatch `refresh_igdb_games_job.IgdbClient.create`, `...create_db_session`, and `job._acquire_lock`.
- Distro API facts (verified against `azure-sdk-for-python` source):
  - `configure_azure_monitor(**kwargs)` accepts `connection_string`, `span_processors`, `timeout`, `disable_offline_storage`, `storage_directory`.
  - Sampler defaults from `OTEL_TRACES_SAMPLER`; **unset → rate-limited 5 spans/sec**, which violates the 100%-default AC. `parentbased_trace_id_ratio` + `OTEL_TRACES_SAMPLER_ARG` (default ratio `1.0` when arg missing) gives 100% and env-only tuning.
  - Auto-instruments `fastapi`, `requests` (covers `steam_web_api`), and recent versions also `httpx`; **never** sqlalchemy/pyodbc.
  - `configure_azure_monitor` swaps `fastapi.FastAPI` at configure time and adds an OTel `LoggingHandler` to the root logger (all propagating `logger.*` records get bridged with trace context).
  - `TracerProvider` registers an `atexit` flush; lifespan shutdown gives us an explicit bounded flush too.
- httpx and requests instrumentations set `http.url` **at span start** (passed as `attributes=` to `start_as_current_span`) → an `on_start` span processor can rewrite it before export. The distro's built-in `redact_url()` only covers AWS-style params, **not** `key`/`token`.
- Offline storage default: `<tempfile.gettempdir()>/Microsoft/AzureMonitor/...` (falls back to `/tmp`, which is `1777` and writable by non-root `appuser`).

## Files to Modify/Create

| File | Action |
|---|---|
| `backend/pyproject.toml` (+ `uv.lock`) | Modify — `uv add azure-monitor-opentelemetry opentelemetry-instrumentation-sqlalchemy opentelemetry-instrumentation-httpx` |
| `backend/app/settings.py` | Modify — add `applicationinsights_connection_string: str = ""` |
| `backend/app/telemetry.py` | **Create** — config, redaction processor, helpers |
| `backend/app/lifespan.py` | **Create** — chained lifespan |
| `backend/main.py` | Modify — use `app_lifespan` |
| `backend/app/database/engine.py` | Modify — instrument engine at creation |
| `backend/app/features/auth/get_current_user.py` | Modify — `record_user_identity()` |
| `backend/app/features/admin/refresh_igdb_games_job.py` | Modify — root job span |
| `backend/app/features/user/cover_fetcher.py` | Modify — child span |
| `backend/app/features/user/genre_fetcher.py` | Modify — child span |
| `backend/app/features/user/platform_fetcher.py` | Modify — child span |
| `backend/app/features/health/get_readiness_handler.py` | Modify — `telemetry` field |
| `backend/.env.sample` | Modify — new var + commented OTEL vars |
| `.github/workflows/deploy-to-azure-app-service.yml` | Modify — optional-var sync |
| `backend/tests/test_telemetry.py` | **Create** |
| `backend/tests/features/health/test_get_readiness_handler.py` | Modify |
| `backend/tests/features/admin/test_refresh_igdb_games_job.py` | Modify — job span test |

No DB migrations, no frontend code changes (codegen only — the readiness response model changed).

## Step-by-Step Instructions

### Step 1 — Dependencies

```bash
cd backend
uv add azure-monitor-opentelemetry opentelemetry-instrumentation-sqlalchemy opentelemetry-instrumentation-httpx
```

`opentelemetry-instrumentation-httpx` is an explicit dependency so the manual fallback import always resolves; if the installed distro already auto-instruments httpx we skip our call (see Step 3).

### Step 2 — Settings

In `backend/app/settings.py`, add below `steam_api_key`:

```python
    applicationinsights_connection_string: str = ""
```

Empty default — required fields would break `export_openapi.py`, the Dockerfile OpenAPI stage's dummy envs, `tests/conftest.py`, and the workflow validate block. No Dockerfile/conftest changes needed.

### Step 3 — Create `backend/app/telemetry.py`

```python
"""OpenTelemetry telemetry export to Azure Application Insights."""

from __future__ import annotations

import logging
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import Span, Tracer

from app.settings import get_settings

logger = logging.getLogger(__name__)

_CREDENTIAL_QUERY_PARAMS = frozenset(
    {"key", "apikey", "api_key", "access_token", "token"}
)
_REDACTED = "REDACTED"
_URL_ATTRIBUTE_KEYS = ("http.url", "url.full", "http.target", "url.query")

_enabled = False


def redact_credentials(url: str) -> str:
    """Replace credential-bearing values in a URL.

    Redacts query parameter values for credential-style parameter names and
    any userinfo portion of the authority. Path, host, fragment, and all
    other query parameters are preserved.

    Args:
        url: URL captured on a span attribute.

    Returns:
        The URL with credential values replaced by "REDACTED".
    """
    parts = urlsplit(url)
    netloc = parts.netloc
    if "@" in netloc:
        netloc = f"{_REDACTED}@{netloc.rsplit('@', 1)[1]}"

    query_pairs = parse_qsl(parts.query, keep_blank_values=True)
    if not any(name.lower() in _CREDENTIAL_QUERY_PARAMS for name, _ in query_pairs):
        if netloc == parts.netloc:
            return url
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

    redacted_query = urlencode(
        [
            (name, _REDACTED if name.lower() in _CREDENTIAL_QUERY_PARAMS else value)
            for name, value in query_pairs
        ]
    )
    return urlunsplit(
        (parts.scheme, netloc, parts.path, redacted_query, parts.fragment)
    )


class CredentialRedactingSpanProcessor(SpanProcessor):
    """Rewrites credential-bearing URL attributes on spans before export."""

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        """Redact URL attributes on a newly started recording span.

        Called at span start because SDK span attributes become immutable the
        moment the span ends, and httpx/requests instrumentations set their
        URL attributes when the span is created.

        Args:
            span: The recording span being started.
            parent_context: Ignored; required by the SpanProcessor interface.
        """
        attributes = span.attributes
        if not attributes:
            return
        for key in _URL_ATTRIBUTE_KEYS:
            value = attributes.get(key)
            if isinstance(value, str):
                redacted = redact_credentials(value)
                if redacted != value:
                    span.set_attribute(key, redacted)


def configure_telemetry(app: FastAPI) -> None:
    """Configure OpenTelemetry export to Azure Application Insights.

    No-op when APPLICATIONINSIGHTS_CONNECTION_STRING is unset, so the app
    behaves exactly as before. Never raises: any setup failure (invalid
    connection string, missing package, exporter init error) is logged once
    and leaves telemetry disabled.

    Args:
        app: The FastAPI application to instrument.
    """
    global _enabled
    settings = get_settings()
    if not settings.applicationinsights_connection_string:
        return

    try:
        os.environ.setdefault("OTEL_SERVICE_NAME", "backlog-boss")
        os.environ.setdefault("OTEL_TRACES_SAMPLER", "parentbased_trace_id_ratio")
        os.environ.setdefault("OTEL_TRACES_SAMPLER_ARG", "1.0")

        # Imported lazily so a broken/missing Azure package cannot crash app import.
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string,
            span_processors=[CredentialRedactingSpanProcessor()],
        )

        # The app was instantiated at import time, before the distro swapped
        # fastapi.FastAPI, so it is not covered by auto-instrumentation.
        FastAPIInstrumentor().instrument_app(app)

        httpx_instrumentor = HTTPXClientInstrumentor()
        if not getattr(httpx_instrumentor, "_is_instrumented_by_opentelemetry", False):
            httpx_instrumentor.instrument()

        _enabled = True
    except Exception:
        logger.exception(
            "Telemetry configuration failed; continuing without telemetry"
        )
        _enabled = False


def shutdown_telemetry() -> None:
    """Flush pending telemetry and shut down the OpenTelemetry providers.

    Safe to call when telemetry was never configured. Each provider is shut
    down independently and failures are swallowed so shutdown never blocks or
    crashes the process. The TracerProvider also registers an atexit flush as
    a backstop; provider shutdown is idempotent.
    """
    global _enabled
    if not _enabled:
        return

    from opentelemetry._logs import get_logger_provider

    for get_provider in (trace.get_tracer_provider, get_logger_provider):
        try:
            provider = get_provider()
            shutdown = getattr(provider, "shutdown", None)
            if callable(shutdown):
                shutdown()
        except Exception:
            logger.exception("Failed to shut down telemetry provider")

    _enabled = False


def is_telemetry_enabled() -> bool:
    """Return whether telemetry was successfully configured this process."""
    return _enabled


def get_tracer(name: str) -> Tracer:
    """Return a tracer for the given instrumentation scope.

    Args:
        name: Instrumentation scope name, usually ``__name__``.

    Returns:
        A tracer that yields no-op spans when telemetry is not configured.
    """
    return trace.get_tracer(name)


def instrument_engine(engine: "Engine") -> None:
    """Attach SQLAlchemy instrumentation to an engine when telemetry is enabled.

    The distro does not cover pyodbc, so this is the only SQLAlchemy
    instrumentation. Called once per process because ``get_db_engine`` is
    lru_cached; tests run with telemetry disabled so this is inert there.

    Args:
        engine: The SQLAlchemy engine created by ``get_db_engine``.
    """
    if not _enabled:
        return
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(engine=engine)


def record_user_identity(app_user_id: int, steam_id: str) -> None:
    """Attach user identity attributes to the active span, if recording.

    No-op when no span is active or telemetry is disabled, so callers need
    no guards.

    Args:
        app_user_id: Internal application user id.
        steam_id: Steam id of the user.
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute("user.id", app_user_id)
        span.set_attribute("user.steam_id", steam_id)
```

Notes:

- `Engine` type import: add `from sqlalchemy.engine import Engine` under `TYPE_CHECKING` (or plain import) so the signature is real — adjust imports accordingly; the docstring above uses the string form for brevity.
- Redaction runs in `on_start`, which the provider invokes for every span because the processor is registered via the `span_processors` kwarg — it executes before the distro's `BatchSpanProcessor` exports.
- `get_tracer` exists as a seam so tests can monkeypatch tracers without touching the global provider (`set_tracer_provider` is set-once per process — never set it in tests).
- `_enabled` starts `False`; only the success path of `configure_telemetry` flips it.

### Step 4 — Chained lifespan

Create `backend/app/lifespan.py`:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.http_client import configure_httpx_lifespan
from app.telemetry import configure_telemetry, shutdown_telemetry


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run application startup and shutdown hooks.

    Configures telemetry before the shared HTTP client is created so client
    spans are captured, then flushes telemetry during shutdown.

    Args:
        app: The FastAPI application being served.

    Yields:
        Control to the server while the application is running.
    """
    configure_telemetry(app)
    try:
        async with configure_httpx_lifespan(app):
            yield
    finally:
        shutdown_telemetry()
```

In `backend/main.py`: replace `from app.http_client import configure_httpx_lifespan` with `from app.lifespan import app_lifespan`, and change `lifespan=configure_httpx_lifespan` → `lifespan=app_lifespan`. Leave `logging.basicConfig` (line 16) untouched.

### Step 5 — Engine instrumentation

In `backend/app/database/engine.py`:

```python
from app.telemetry import instrument_engine

@lru_cache
def get_db_engine() -> Engine:
    """Create the cached database engine and attach telemetry instrumentation.

    Returns:
        The shared SQLAlchemy engine for the application.
    """
    engine = create_engine(create_connection_url(get_settings()))
    instrument_engine(engine)
    return engine
```

No import cycle: `app.telemetry` imports only `app.settings`.

### Step 6 — User identity on spans

In `backend/app/features/auth/get_current_user.py`, add `from app.telemetry import record_user_identity` and call it before returning the resolved user (inside `get_current_user`, after the `app_session` lookup succeeds):

```python
    record_user_identity(app_user.app_user_id, app_user.steam_id)

    return User(
        app_user_id=app_user.app_user_id,
        steam_id=app_user.steam_id,
        persona_name=app_user.persona_name,
        first_name=app_user.first_name,
        last_name=app_user.last_name,
    )
```

`require_current_user` gets it transitively (it depends on `get_current_user`). During a request the FastAPI/ASGI server span is active, so attributes land on it; without telemetry the call is a no-op.

### Step 7 — Root job span

In `backend/app/features/admin/refresh_igdb_games_job.py`, add imports:

```python
from opentelemetry.context import Context

from app.telemetry import get_tracer
```

Wrap the **entire existing body** of `run()` (indented one level) in a root span:

```python
    def run(self, app_user_id: int) -> None:
        """Execute the refresh job.

        Args:
            app_user_id: Id of the admin user who triggered the refresh.
                Recorded on the lock row to satisfy the FK to AppUser.
        """
        with get_tracer(__name__).start_as_current_span(
            "job.refresh_igdb_games",
            context=Context(),
            attributes={"job.name": "refresh_igdb_games", "user.id": app_user_id},
        ):
            igdb_client = IgdbClient.create()

            with create_db_session() as db:
                try:
                    ...existing body unchanged...
```

- `context=Context()` forces a **root** span so the job produces its own trace (without it, Starlette runs `BackgroundTasks` inside the ASGI call and the span would be a child of the request span, failing the "own traces" AC).
- Existing `return` statements inside the `with` are fine — the context manager exits normally.
- Exceptions propagate as before; the span context manager records them as span events (default behavior).

### Step 8 — Fetcher child spans

Each of `cover_fetcher.py`, `genre_fetcher.py`, `platform_fetcher.py` exposes `fetch_and_persist(game_ids)`. Wrap the method body (keep the existing docstring) in:

```python
        with get_tracer(__name__).start_as_current_span("fetch.covers"):
```

(span names: `fetch.covers`, `fetch.genres`, `fetch.platforms`). Add `from app.telemetry import get_tracer` to each file. These run in-request, so the spans are children of the server span — they give the fetchers named visibility without extra plumbing.

### Step 9 — Readiness reports telemetry state

In `backend/app/features/health/get_readiness_handler.py`:

```python
from app.telemetry import is_telemetry_enabled

class GetReadinessResponse(ApiResponseModel):
    message: str
    telemetry: str
```

and in `handle()`:

```python
        return GetReadinessResponse(
            message="Database is ready.",
            telemetry="enabled" if is_telemetry_enabled() else "disabled",
        )
```

Liveness untouched. The field name is identical in snake/camel case, so no alias needed.

### Step 10 — Deploy surface

`backend/.env.sample` — append:

```
APPLICATIONINSIGHTS_CONNECTION_STRING=

# Optional OpenTelemetry tuning (read by the Azure Monitor distro)
# OTEL_SERVICE_NAME=backlog-boss
# OTEL_TRACES_SAMPLER=parentbased_trace_id_ratio
# OTEL_TRACES_SAMPLER_ARG=1.0
```

`.github/workflows/deploy-to-azure-app-service.yml` — copy the `BASE_URL` optional pattern:

1. In the `"Sync App Service app settings from GitHub"` step's `env:` block (near line 188), add:
   ```yaml
   APPLICATIONINSIGHTS_CONNECTION_STRING: ${{ secrets.APPLICATIONINSIGHTS_CONNECTION_STRING }}
   ```
2. After the `BASE_URL` append block (lines 208-210), add:
   ```bash
   if [ -n "${APPLICATIONINSIGHTS_CONNECTION_STRING}" ]; then
     APP_SETTINGS+=("APPLICATIONINSIGHTS_CONNECTION_STRING=${APPLICATIONINSIGHTS_CONNECTION_STRING}")
   fi
   ```
3. In the delete-if-empty block (lines 219-235), add `APPLICATIONINSIGHTS_CONNECTION_STRING` to `DELETE_SETTINGS`.

Do **not** add it to `REQUIRED_VARS` (lines 67-80) or the validate step env — the empty default keeps it optional. Creating the App Insights resource and the GitHub secret is a manual, out-of-scope step.

### Step 11 — Tests

#### New: `backend/tests/test_telemetry.py`

```python
import os

import pytest
from fastapi import FastAPI
from opentelemetry.sdk.trace import TracerProvider

from app import settings as settings_module
from app import telemetry
from app.settings import clear_settings_cache
from app.telemetry import (
    CredentialRedactingSpanProcessor,
    record_user_identity,
    redact_credentials,
)

_OTEL_ENV_KEYS = (
    "APPLICATIONINSIGHTS_CONNECTION_STRING",
    "OTEL_SERVICE_NAME",
    "OTEL_TRACES_SAMPLER",
    "OTEL_TRACES_SAMPLER_ARG",
)


@pytest.fixture(autouse=True)
def _restore_telemetry_state():
    saved_env = {key: os.environ.get(key) for key in _OTEL_ENV_KEYS}
    saved_enabled = telemetry._enabled
    yield
    telemetry._enabled = saved_enabled
    for key, value in saved_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    clear_settings_cache()


@pytest.fixture
def connection_string(monkeypatch):
    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=00000000-0000-0000-0000-000000000000;"
        "IngestionEndpoint=https://example.invalid/",
    )
    clear_settings_cache()
    yield
    clear_settings_cache()
```

Test cases:

1. **`test_configure_telemetry_is_noop_without_connection_string`** — monkeypatch `azure.monitor.opentelemetry.configure_azure_monitor` with a recorder; call `telemetry.configure_telemetry(FastAPI())`; assert not called and `telemetry.is_telemetry_enabled()` is `False`.
2. **`test_configure_telemetry_enables_and_passes_processor`** (uses `connection_string`) — monkeypatch `azure.monitor.opentelemetry.configure_azure_monitor`, `opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app`, and `opentelemetry.instrumentation.httpx.HTTPXClientInstrumentor.instrument` to recorders; call `configure_telemetry(FastAPI())`; assert enabled, `connection_string` kwarg contains `InstrumentationKey`, `span_processors[0]` is a `CredentialRedactingSpanProcessor`, both instrumentor calls made, and `os.environ["OTEL_TRACES_SAMPLER"] == "parentbased_trace_id_ratio"`.
3. **`test_configure_telemetry_sampler_env_not_overridden`** (uses `connection_string`) — `monkeypatch.setenv("OTEL_TRACES_SAMPLER", "always_on")` before calling configure; assert the value is unchanged afterwards (setdefault semantics).
4. **`test_configure_telemetry_fail_soft`** (uses `connection_string`) — monkeypatch `configure_azure_monitor` to `raise RuntimeError("bad")`; assert `configure_telemetry` does not raise and stays disabled.
5. **`test_redact_credentials`** — parametrized:
   - `.../v1/?key=SECRET&format=json` → `key=REDACTED`, `format=json` kept;
   - `?apikey=SECRET`, `?access_token=SECRET`, `?token=SECRET`, case-insensitive `?Key=SECRET`;
   - multiple params (`?key=SECRET&token=SECRET&x=1`);
   - no query → string returned unchanged (identity);
   - `https://user:pass@example.com/path` → `https://REDACTED@example.com/path`;
   - host/path preserved in every case.
6. **`test_span_processor_redacts_url_on_start`** — build a **local** `TracerProvider()` (never set the global one — `set_tracer_provider` is set-once per process), `tracer.start_span("x", attributes={"http.url": "https://api.steampowered.com/v1/?key=SECRET", "http.method": "GET"})`, call `CredentialRedactingSpanProcessor().on_start(span, None)`, assert `span.attributes["http.url"] == "https://api.steampowered.com/v1/?key=REDACTED"` and `http.method` untouched; then `span.end()` and `provider.shutdown()`.
7. **`test_record_user_identity_sets_attributes`** — same local-provider pattern: inside `with tracer.start_as_current_span("req") as span:` call `record_user_identity(42, "76561198000000000")`; assert `span.attributes["user.id"] == 42` and `user.steam_id`.
8. **`test_record_user_identity_noop_without_span`** — call with no active span; must not raise.
9. **`test_instrument_engine_skipped_when_disabled`** — monkeypatch `opentelemetry.instrumentation.sqlalchemy.SQLAlchemyInstrumentor` with a recorder; call `telemetry.instrument_engine(object())`; assert not called. Then set `telemetry._enabled = True`, call again, assert called with `engine=` kwarg (the autouse fixture restores the flag).
10. **`test_shutdown_telemetry_is_safe_when_disabled`** — `telemetry.shutdown_telemetry()` with `_enabled = False` must not raise.

#### Modify: `backend/tests/features/health/test_get_readiness_handler.py`

- Update the success assertion to `GetReadinessResponse(message="Database is ready.", telemetry="disabled")` (telemetry is off in tests).
- Add `test_handle_reports_telemetry_enabled`: monkeypatch `app.features.health.get_readiness_handler.is_telemetry_enabled` to return `True`; assert `actual.telemetry == "enabled"`.

#### Modify: `backend/tests/features/admin/test_refresh_igdb_games_job.py`

Add a job-span test following the existing `test_run_skips_when_lock_is_held` setup (mock `IgdbClient.create`, `create_db_session`, `_acquire_lock`) plus a fake tracer:

```python
def test_run_creates_root_job_span(db_session: Session, mocker: MockerFixture):
    from app.features.admin import refresh_igdb_games_job as job_module

    captured = {}

    class _FakeSpan:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    class _FakeTracer:
        def start_as_current_span(self, name, **kwargs):
            captured["name"] = name
            captured.update(kwargs)
            return _FakeSpan()

    mocker.patch.object(job_module, "get_tracer", lambda _name: _FakeTracer())
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.IgdbClient.create",
        return_value=mocker.Mock(),
    )
    mocker.patch(
        "app.features.admin.refresh_igdb_games_job.create_db_session",
        side_effect=lambda: _fake_db_session(db_session),
    )
    job = RefreshIgdbGamesJob()
    mocker.patch.object(job, "_acquire_lock", return_value=False)
    app_user = _create_app_user(db_session)

    job.run(app_user.app_user_id)

    assert captured["name"] == "job.refresh_igdb_games"
    assert captured["context"] == Context()          # from opentelemetry.context
    assert captured["attributes"]["job.name"] == "refresh_igdb_games"
    assert captured["attributes"]["user.id"] == app_user.app_user_id
```

### Step 12 — Verify

```bash
cd backend
uv run ruff check . && uv run ruff format .
uv run pytest -q
uv run python export_openapi.py && cd ../frontend && npm run genclient
```

Then:

```bash
docker build -t backlog-boss .
```

- Confirms the new optional setting needs no Dockerfile dummy-env change.
- Offline storage: confirm the exporter's default temp dir is writable for `appuser` (should be `/tmp`, mode 1777). If a smoke run shows otherwise, pass `storage_directory=` (or `disable_offline_storage=True`) to `configure_azure_monitor`.

Manual smoke (optional, needs any syntactically valid connection string): run `uv run fastapi dev main.py` with `APPLICATIONINSIGHTS_CONNECTION_STRING` set — app starts, no crash, `/api/health/readiness` reports `telemetry: "enabled"`; without the var it reports `"disabled"` and console output is byte-identical to today. Real export verification against an App Insights resource is out of scope (resource creation is a manual step).

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Setup location | Chained lifespan (`app_lifespan`) | Matches the issue's dev note; config at import would also run for `export_openapi.py` |
| FastAPI spans | Manual `instrument_app(app)` after configure | App is created at import, before the distro's `fastapi.FastAPI` class swap |
| Redaction | `SpanProcessor.on_start` via `span_processors` kwarg | SDK attributes freeze at span end; httpx/requests set URLs at span start; processor runs before the exporting `BatchSpanProcessor` |
| Redaction values | `REDACTED` (URL-safe) | `urlencode` leaves it unescaped — readable in App Insights |
| Sampler default | `setdefault("OTEL_TRACES_SAMPLER", "parentbased_trace_id_ratio")` + `OTEL_TRACES_SAMPLER_ARG=1.0` | Distro's own default is rate-limited 5 spans/sec (fails the 100% AC); `setdefault` = env-only tuning, no code change to lower it |
| httpx | Explicit dep; `instrument()` only if the singleton isn't already instrumented | Distro versions differ on httpx support; `BaseInstrumentor` singletons make the check deterministic |
| SQLAlchemy | Manual `instrument_engine` at engine creation | Distro never covers pyodbc/sqlalchemy; engine is `@lru_cache`d → one call per process; guarded by `_enabled` so tests are inert |
| Azure imports | Lazy, inside `configure_telemetry` try-block | A broken/missing package can never crash app import (fail-soft) |
| Job parentage | Explicit root `Context()` | AC requires job runs to produce *their own* traces; background tasks otherwise inherit the request span |
| User attributes | `record_user_identity` called from `get_current_user` | Only place identity is resolved; no middleware exists; no-op when disabled |
| Fetcher spans | Named child spans (`fetch.covers` etc.) | Fetchers run in-request (not background) — children of the server span give visibility with no extra plumbing |
| Health field | Readiness only | Explicit user decision for issue #81 |
| Failure mode | Whole configure wrapped in try/except, flag flips only on success | Invalid connection string / unreachable endpoint never affects requests; one log line at startup |
| Shutdown | Lifespan `finally` shuts down tracer + logger providers | Bounded, idempotent flush on App Service restart; `atexit` remains as backstop |

## Edge Cases

- **No connection string** → `configure_telemetry` returns before any Azure import; console logging, tests, codegen, and Docker build are byte-identical to today; no Azure credentials ever needed in CI.
- **Invalid connection string** → exporter init raises inside `configure_azure_monitor`; caught, logged once at startup, `_enabled` stays `False`, app serves normally.
- **`httpx` logger stays disabled** (`http_client.py:9`) → logger-level disable means those records never reach the OTel `LoggingHandler` on the root logger; the Steam client-secret guard is preserved.
- **Headers/cookies/bodies/SQL params** → never captured: no header-capture env vars are configured, and pyodbc statements use `?` placeholders so `db.statement` contains no bound values.
- **Attribute re-encoding** → `redact_credentials` rebuilds the query only when a credential param is present; non-credential params may be percent-normalized (semantically identical). Path and host are always preserved.
- **Engine created before configure** → impossible: engine creation is lazy and configure runs at startup before any request. `reset_db_engine()` runs only in tests, where telemetry is disabled.
- **`SQLAlchemyInstrumentor` singleton** → `instrument()` is once-per-process; that matches the single cached engine. If a future change creates a second engine with telemetry on, add a per-engine guard at that point.
- **Unreachable App Insights endpoint** → batching (≈5s) plus the distro's rate-limited diagnostic logging keep errors off the per-request path; verify during the smoke run that failures are not logged per request.
- **Shutdown hang** → provider `shutdown()` is bounded by the exporter timeout and wrapped in try/except; if verification shows flush exceeds ~5s, pass `timeout=5000` to `configure_azure_monitor`.
- **Offline storage path** → defaults under `tempfile.gettempdir()` (`/tmp`, writable by `appuser`); verified in the Docker step with a documented fallback.
- **Sampling tuning** → operators set `OTEL_TRACES_SAMPLER_ARG=0.1` (and optionally `OTEL_TRACES_SAMPLER`) as App Service app settings; `setdefault` never overrides an existing value.
- **Never set the global tracer provider in tests** → `set_tracer_provider` is set-once per process and would leak across the suite; tests use local `TracerProvider()` instances or monkeypatch `get_tracer`.
