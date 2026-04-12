from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AppSession, AppUser
from app.features.auth.logout_handler import LogoutHandler


def _create_request_with_session_key(session_key: str | None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if session_key is not None:
        headers.append((b"cookie", f"session_key={session_key}".encode()))

    return Request({"type": "http", "headers": headers})


def test_handle_deletes_matching_session_and_clears_cookie(db_session: Session):
    app_user = AppUser(
        steam_id="76561198000000000",
        persona_name="Test Persona",
        first_name=None,
        last_name=None,
    )
    app_session = AppSession(
        app_session_key=uuid4(),
        expiration_date=datetime.now(timezone.utc) + timedelta(days=1),
        app_user=app_user,
    )
    db_session.add(app_user)
    db_session.add(app_session)
    db_session.commit()

    assert (
        db_session.scalars(
            select(AppSession).where(
                AppSession.app_session_key == app_session.app_session_key
            )
        ).one_or_none()
        is not None
    )

    handler = LogoutHandler(
        db_session,
        _create_request_with_session_key(str(app_session.app_session_key)),
    )

    response = handler.handle()

    assert (
        db_session.scalars(
            select(AppSession).where(
                AppSession.app_session_key == app_session.app_session_key
            )
        ).one_or_none()
        is None
    )
    assert response.headers["set-cookie"].startswith("session_key=")
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_handle_clears_cookie_when_session_cookie_is_missing(db_session: Session):
    handler = LogoutHandler(db_session, _create_request_with_session_key(None))

    response = handler.handle()

    assert response.headers["set-cookie"].startswith("session_key=")
    assert "Max-Age=0" in response.headers["set-cookie"]
