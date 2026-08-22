from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import RateLimitHit
from app.infrastructure.rate_limiter import RateLimiter, RateLimitRule

BASE_TIME = datetime(2026, 8, 22, 12, 0, 0, tzinfo=UTC)

RULE = RateLimitRule(max_requests=1, window=timedelta(minutes=1))


def _clock(minutes: float = 0.0):
    return lambda: BASE_TIME + timedelta(minutes=minutes)


def _check(db_session: Session, key: str = "user:1:test-scope", minutes: float = 0.0):
    return RateLimiter(db_session).check(
        key=key,
        rule=RULE,
        now_fn=_clock(minutes),
    )


def test_first_request_allowed(db_session: Session) -> None:
    result = _check(db_session)

    assert result.allowed
    assert result.retry_after_seconds == 0


def test_second_request_same_window_rejected(db_session: Session) -> None:
    assert _check(db_session).allowed

    result = _check(db_session)

    assert not result.allowed
    assert result.retry_after_seconds == 60


def test_rejected_request_does_not_increment(db_session: Session) -> None:
    assert _check(db_session).allowed
    assert not _check(db_session).allowed

    stmt = select(RateLimitHit).where(
        RateLimitHit.rate_limit_key == "user:1:test-scope"
    )
    hit = db_session.scalars(stmt).one()

    assert hit.hit_count == 1


def test_next_window_allows_again(db_session: Session) -> None:
    assert _check(db_session, minutes=0).allowed

    result = _check(db_session, minutes=1.0)

    assert result.allowed

    stmt = select(RateLimitHit).where(
        RateLimitHit.rate_limit_key == "user:1:test-scope"
    )
    hits = db_session.scalars(stmt).all()

    # The old window's row is removed by opportunistic cleanup.
    assert len(hits) == 1
    assert hits[0].window_start == BASE_TIME + timedelta(minutes=1)


def test_old_windows_cleaned_up(db_session: Session) -> None:
    previous_window_start = BASE_TIME - timedelta(minutes=1)
    db_session.add(
        RateLimitHit(
            rate_limit_key="user:1:test-scope",
            window_start=previous_window_start,
            hit_count=1,
        )
    )
    db_session.commit()

    assert _check(db_session).allowed

    stmt = (
        select(RateLimitHit)
        .where(RateLimitHit.rate_limit_key == "user:1:test-scope")
        .where(RateLimitHit.window_start < BASE_TIME)
    )
    remaining = db_session.scalars(stmt).all()

    assert remaining == []


def test_keys_are_isolated(db_session: Session) -> None:
    assert _check(db_session, key="user:1:a").allowed
    assert not _check(db_session, key="user:1:a").allowed
    assert _check(db_session, key="user:2:b").allowed

    stmt = select(RateLimitHit.rate_limit_key)
    keys = set(db_session.scalars(stmt).all())

    assert keys == {"user:1:a", "user:2:b"}
