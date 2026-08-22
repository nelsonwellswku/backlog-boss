# API Rate Limiting — Technical Implementation Plan

## Goal

Add database-backed fixed-window rate limiting to `POST /api/user/refresh-my-backlog` (1 request per minute per user), implemented as a reusable FastAPI dependency in `app/infrastructure/` so other endpoints can adopt it by adding one line to their route declaration.

## Current State

- `POST /api/user/refresh-my-backlog` is declared at `backend/app/features/user/user_router.py:39-43`. It injects `RefreshMyBacklogHandler` via bare `Depends()`; auth happens inside the handler's constructor through `RequiredCurrentUser` (`backend/app/features/auth/get_current_user.py:50-57`, raises 401 when unauthenticated).
- `get_current_user()` (`backend/app/features/auth/get_current_user.py:21`) takes `(request, db)` and returns `User | None`; FastAPI's per-request dependency cache means multiple dependencies resolving it share one DB query.
- `DbSession` (`backend/app/database/engine.py:66`) yields a plain `Session`; there is no per-request transaction wrapper — handlers call `db.commit()` themselves.
- `create_db_session()` (`backend/app/database/engine.py:51`) opens a standalone session outside DI.
- ORM models live in `backend/app/database/models.py` with `Base(DeclarativeBase)` using `MetaData(schema="bb")`, PascalCase column names, `BigInteger Identity()` PKs (see `AppSession` at line 28), and `DATETIMEOFFSET` timestamps.
- Migrations are plain SQL files `migrations/up/0001.sql` … `0011.sql` applied by Grate. Latest is `migrations/up/0011.sql`.
- Tests use Testcontainers-backed real SQL Server: session-scoped `database_container` fixture + `db_session` fixture that wraps each test in a rolled-back outer transaction (`Session(bind=connection, join_transaction_mode="create_savepoint")`) — inner `session.commit()` calls commit only a savepoint, so tests stay isolated.
- No middleware, no rate limiting, no background-job infrastructure exists today.

## Files to Modify/Create

| File | Action |
|------|--------|
| `migrations/up/0012.sql` | Create — `bb.RateLimitHit` table |
| `backend/app/database/models.py` | Modify — add `RateLimitHit` model |
| `backend/app/infrastructure/rate_limiter.py` | Create — limiter class + dependency factory |
| `backend/app/features/user/user_router.py` | Modify — wire dependency into refresh endpoint |
| `backend/tests/infrastructure/test_rate_limiter.py` | Create — tests |

## Step-by-Step Instructions

### Step 1 — Migration

Create `migrations/up/0012.sql`:

```sql
create table bb.RateLimitHit (
    RateLimitHitId bigint identity not null,
    RateLimitKey nvarchar(450) not null,
    WindowStart datetimeoffset not null,
    HitCount int not null,
    constraint PK_RateLimitHit primary key (RateLimitHitId),
    constraint UQ_RateLimitHit_Key_Window unique (RateLimitKey, WindowStart)
);
```

Key details:
- `RateLimitKey` avoids SQL keyword brackets entirely.
- The unique constraint doubles as the lookup index for `(RateLimitKey, WindowStart)` — no separate index needed.
- Rows accumulate one per key per window; old rows are deleted opportunistically (Step 3).

### Step 2 — ORM model

In `backend/app/database/models.py`, add (following existing conventions):

```python
class RateLimitHit(Base):
    __tablename__ = "RateLimitHit"

    rate_limit_hit_id: Mapped[int] = mapped_column(
        "RateLimitHitId", BigInteger, Identity(), primary_key=True
    )
    rate_limit_key: Mapped[str] = mapped_column("RateLimitKey", String(450))
    window_start: Mapped[datetime] = mapped_column("WindowStart", DATETIMEOFFSET)
    hit_count: Mapped[int] = mapped_column("HitCount", Integer)

    __table_args__ = (
        UniqueConstraint("RateLimitKey", "WindowStart", name="UQ_RateLimitHit_Key_Window"),
    )
```

Add any missing imports (`UniqueConstraint` from `sqlalchemy`, `Integer` from `sqlalchemy`) alongside the existing ones at the top of the file.

### Step 3 — Rate limiter infrastructure

Create `backend/app/infrastructure/rate_limiter.py`:

```python
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, TypeAlias

from fastapi import Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.engine import DbSession
from app.database.models import RateLimitHit
from app.features.auth.get_current_user import RequiredCurrentUser


@dataclass(frozen=True)
class RateLimitRule:
    max_requests: int
    window: timedelta


@dataclass(frozen=True)
class RateLimiterResult:
    allowed: bool
    retry_after_seconds: int


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _window_start(now: datetime, window: timedelta) -> datetime:
    epoch_seconds = int(now.timestamp())
    window_seconds = int(window.total_seconds())
    floored = epoch_seconds - (epoch_seconds % window_seconds)
    return datetime.fromtimestamp(floored, tz=timezone.utc)


class RateLimiter:
    def check(
        self,
        db: Session,
        key: str,
        rule: RateLimitRule,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> RateLimiterResult:
        """Check the rate limit for a key and consume one slot if allowed.

        Runs in its own short transaction: commits before returning so locks
        are never held while the caller's business logic executes. Rejected
        requests do not increment the counter.

        Args:
            db: Session used for the counter transaction.
            key: Fully-qualified storage key (identity + scope).
            rule: Max requests allowed per aligned window.
            now_fn: Clock source; overridable in tests.

        Returns:
            Whether the request is allowed and how long until the window resets.
        """
        now = now_fn()
        window_start = _window_start(now, rule.window)
        window_end = window_start + rule.window

        hit = RateLimitHit(rate_limit_key=key, window_start=window_start, hit_count=0)
        db.add(hit)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()

        stmt = (
            select(RateLimitHit)
            .where(RateLimitHit.rate_limit_key == key)
            .where(RateLimitHit.window_start == window_start)
        )
        hit = db.scalars(
            stmt.with_hint(RateLimitHit, "WITH (UPDLOCK, ROWLOCK)", dialect_name="mssql")
        ).one()

        if hit.hit_count >= rule.max_requests:
            db.commit()  # release locks without incrementing
            return RateLimiterResult(
                allowed=False,
                retry_after_seconds=max(1, int((window_end - now).total_seconds())),
            )

        hit.hit_count += 1
        db.execute(
            delete(RateLimitHit)
            .where(RateLimitHit.rate_limit_key == key)
            .where(RateLimitHit.window_start < window_start)
        )
        db.commit()
        return RateLimiterResult(allowed=True, retry_after_seconds=0)


def limited(scope: str, rule: RateLimitRule):
    """Build a FastAPI dependency enforcing a per-user rate limit.

    Args:
        scope: Name of the protected operation; part of the storage key.
        rule: Max requests allowed per user per window.

    Returns:
        A dependency callable suitable for ``dependencies=[...]``.
    """

    def _dep(db: DbSession, current_user: RequiredCurrentUser) -> None:
        key = f"user:{current_user.app_user_id}:{scope}"
        result = RateLimiter().check(db, key=key, rule=rule)
        if not result.allowed:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many requests. Try again later.",
                headers={"Retry-After": str(result.retry_after_seconds)},
            )

    return _dep
```

Key details:
- **Own short transaction**: `check()` commits (or releases locks) before returning, so the UPDLOCK is never held during the handler's Steam/IGDB work. Committing the shared request session here is safe — handlers commit explicitly anyway.
- **Insert-first**: adding the row and flushing resolves "does this window's row exist" in one shot; a concurrent replica's insert loses via `IntegrityError` and rolls back, then re-selects under lock.
- **UPDLOCK select**: serializes check-and-increment across replicas. SQLAlchemy renders MSSQL table hints via `with_hint(..., dialect_name="mssql")`.
- **Rejected ≠ incremented**: rejection commits only to release the lock; `HitCount` untouched, cleanup skipped.
- **Opportunistic cleanup** runs on the allow path only, keeping ≤ ~2 rows per key forever.
- **Epoch-floored windows** align to clock boundaries for any window size and are identical across replicas regardless of which server computes them (app-side UTC).
- `RequiredCurrentUser` in `_dep`: unauthenticated requests fail with 401 before any counter logic; FastAPI's dependency cache shares this resolution with the handler's own injection — one auth query total.
- DB errors propagate uncaught (fail loud) — if the DB is down, the handler would fail immediately after anyway.

### Step 4 — Wire into the router

In `backend/app/features/user/user_router.py`, add the import and decorate the endpoint:

```python
from datetime import timedelta

from app.infrastructure.rate_limiter import limited
# ... existing imports ...

@user_router.post(
    "/api/user/refresh-my-backlog",
    dependencies=[
        Depends(
            limited(
                scope="refresh-my-backlog",
                rule=RateLimitRule(max_requests=1, window=timedelta(minutes=1)),
            )
        )
    ],
)
def refresh_my_backlog(
    handler: RefreshMyBacklogHandler = Depends(),
) -> RefreshMyBacklogResponse:
    return handler.handle()
```

(Import `RateLimitRule` from `app.infrastructure.rate_limiter` too.) Protecting future endpoints is exactly this same one-liner with a different scope and rule.

### Step 5 — Tests

Create `backend/tests/infrastructure/test_rate_limiter.py`. All tests use the `db_session` fixture (real SQL Server via Testcontainers; inner commits become savepoints rolled back at teardown). Use an injected `now_fn` instead of sleeping:

```python
from datetime import UTC, datetime, timedelta

BASE_TIME = datetime(2026, 8, 22, 12, 0, 0, tzinfo=UTC)

RULE = RateLimitRule(max_requests=1, window=timedelta(minutes=1))


def _clock(minutes: float = 0.0):
    return lambda: BASE_TIME + timedelta(minutes=minutes)
```

Test cases (call `RateLimiter().check(db_session, key="user:1:test-scope", rule=RULE, now_fn=_clock(...))` directly):

1. **`test_first_request_allowed`** — first check at T returns `allowed=True`.
2. **`test_second_request_same_window_rejected`** — two checks at the same instant: second returns `allowed=False` with `retry_after_seconds == 60`.
3. **`test_rejected_request_does_not_increment`** — reject once, then advance past the window and verify the new window allows again (counter was not inflated); additionally assert the rejected window's row still has `hit_count == 1`.
4. **`test_next_window_allows_again`** — allow at T, allow again at T+60s; both allowed, two rows exist.
5. **`test_old_windows_cleaned_up`** — seed a row for a previous window (insert manually), then make an allowed request in the current window; assert the previous window's row is gone.
6. **`test_keys_are_isolated`** — different keys (`user:1:a`, `user:2:b`) each get their own allowance within the same window.

No TestClient tests — the 429 mapping lives in the thin `_dep` wrapper and follows the existing `HTTPException` pattern.

### Step 6 — Verify

```bash
cd backend && uv run pytest -q tests/infrastructure/test_rate_limiter.py
uv run ruff check . && uv run ruff format .
```

Docker must be running (Testcontainers). No OpenAPI codegen needed — a plain dependency adds nothing to the schema.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Algorithm | Fixed window, clock-aligned | Trivial SQL, burst-at-boundary acceptable for abuse prevention; windows identical across replicas |
| Keying | User id via `RequiredCurrentUser` | Endpoint requires auth; unauthenticated requests get 401 before counting; IP fallback deferred (YAGNI) |
| Enforcement point | Dependency factory `limited(scope, rule)` | Matches repo's thin-routes/DI convention; adopting on a new endpoint is one decorator line |
| Limit config | Inline at endpoint | Values are route-specific behavior like any other code; avoids stringly-typed env parsing |
| Storage shape | Row per `(RateLimitKey, WindowStart)` | Enables opportunistic cleanup without a scheduler |
| Cleanup | Per-key delete of older windows on allow path | No background jobs; bounded growth (~2 rows/key); no cross-replica sweep races |
| Concurrency | Insert-catch-duplicate + `UPDLOCK` select | Honors "rejected ≠ incremented"; lock held milliseconds, committed before handler work |
| Transaction scope | Shared request `DbSession`, committed inside `check()` | Releases locks before expensive IGDB/Steam work; works unchanged against test savepoints |
| DB failure mode | Fail loud (uncaught) | If the DB is down the handler fails right after anyway; no special handling |
| Rejection response | 429 + `Retry-After` header | Standard back-off signal; skipping `X-RateLimit-*` headers until something consumes them |
| Time source | App-side UTC | Millisecond NTP skew irrelevant at minute granularity; no extra round trip |

## Edge Cases

- **Concurrent first requests in a new window**: both try to insert the window's row; one wins, the loser catches `IntegrityError`, rolls back, and re-selects under UPDLOCK. Exactly one increments.
- **Concurrent requests at the limit boundary**: UPDLOCK serializes evaluation — exactly `max_requests` pass per window even across replicas.
- **Clock skew between replicas**: windows are computed from epoch-floored UTC, so ±seconds of skew can shift a request across a boundary but cannot corrupt counts or double-count.
- **DB unavailable**: the exception propagates as an unhandled 500 — acceptable since the handler's own DB access would fail immediately afterward.
- **Test isolation**: the `db_session` fixture's savepoint-based outer transaction absorbs `check()`'s internal commits; everything rolls back at teardown.
- **Unauthenticated callers**: `RequiredCurrentUser` inside the dependency rejects with 401 before any counter row is touched.
- **Frontend behavior**: no changes — React Query surfaces the 429 silently; only abusers notice.
