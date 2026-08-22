from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, TypeAlias

from fastapi import Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.database.engine import DbSession
from app.database.models import RateLimitHit
from app.features.auth.get_current_user import RequiredCurrentUser


@dataclass(frozen=True)
class RateLimitRule:
    """Maximum requests allowed per aligned fixed window."""

    max_requests: int
    window: timedelta


@dataclass(frozen=True)
class RateLimiterResult:
    """Outcome of a rate limit check."""

    allowed: bool
    retry_after_seconds: int


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _window_start(now: datetime, window: timedelta) -> datetime:
    """Floor a timestamp to the start of its containing fixed window.

    Args:
        now: Current UTC timestamp.
        window: Window size.

    Returns:
        UTC timestamp of the window start.
    """
    epoch_seconds = int(now.timestamp())
    window_seconds = int(window.total_seconds())
    floored = epoch_seconds - (epoch_seconds % window_seconds)
    return datetime.fromtimestamp(floored, tz=timezone.utc)


class RateLimiter:
    """Database-backed fixed-window rate limiter."""

    def __init__(self, db: DbSession):
        self.db = db

    def check(
        self,
        key: str,
        rule: RateLimitRule,
        now_fn: Callable[[], datetime] = _utc_now,
    ) -> RateLimiterResult:
        """Check the rate limit for a key and consume one slot if allowed.

        Runs in its own short transaction: commits before returning so locks
        are never held while the caller's business logic executes. Rejected
        requests do not increment the counter.

        Args:
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
        self.db.add(hit)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()

        stmt = (
            select(RateLimitHit)
            .where(RateLimitHit.rate_limit_key == key)
            .where(RateLimitHit.window_start == window_start)
        )
        hit = self.db.scalars(
            stmt.with_hint(
                RateLimitHit, "WITH (UPDLOCK, ROWLOCK)", dialect_name="mssql"
            )
        ).one()

        if hit.hit_count >= rule.max_requests:
            self.db.commit()
            return RateLimiterResult(
                allowed=False,
                retry_after_seconds=max(1, int((window_end - now).total_seconds())),
            )

        hit.hit_count += 1
        self.db.execute(
            delete(RateLimitHit)
            .where(RateLimitHit.rate_limit_key == key)
            .where(RateLimitHit.window_start < window_start)
        )
        self.db.commit()
        return RateLimiterResult(allowed=True, retry_after_seconds=0)


RateLimiterDep: TypeAlias = Annotated[RateLimiter, Depends(RateLimiter)]


class RateLimited:
    """FastAPI dependency enforcing a per-user rate limit.

    Construct once at route declaration time; FastAPI invokes ``__call__``
    per request with its parameters resolved through DI.
    """

    def __init__(self, scope: str, rule: RateLimitRule):
        self.scope = scope
        self.rule = rule

    def __call__(
        self,
        limiter: RateLimiterDep,
        current_user: RequiredCurrentUser,
    ) -> None:
        """Check the caller's rate limit and raise 429 when exceeded.

        Args:
            limiter: Rate limiter bound to the request's DB session.
            current_user: Authenticated user keying the limit.

        Raises:
            HTTPException: 429 with a ``Retry-After`` header when the
                user's allowance for this window is exhausted.
        """
        key = f"user:{current_user.app_user_id}:{self.scope}"
        result = limiter.check(key=key, rule=self.rule)
        if not result.allowed:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many requests. Try again later.",
                headers={"Retry-After": str(result.retry_after_seconds)},
            )
