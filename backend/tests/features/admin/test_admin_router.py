"""Route-level authorization tests for the admin refresh endpoint."""

from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.database.models import AppSession, AppUser, AppUserRole
from main import app

REFRESH_IGDB_GAMES_URL = "/api/admin/refresh-igdb-games"


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Start the FastAPI application so requests run through real routing.

    Yields:
        TestClient bound to the application under test.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session_key_factory(
    database_engine: Engine,
) -> Iterator[Callable[[list[str]], str]]:
    """Create logged-in users holding the given roles, then delete them.

    Rows are committed on their own connection because the ``db_session``
    fixture runs inside a rollback transaction that requests cannot see.

    Args:
        database_engine: Engine connected to the shared test database.

    Yields:
        Function taking role names and returning that user's session cookie value.
    """
    created_user_ids: list[int] = []

    def _create_user(roles: list[str]) -> str:
        session_key = uuid4()
        with Session(database_engine) as session:
            app_user = AppUser(
                steam_id=f"7656{uuid4().hex[:13]}",
                persona_name="Route Test",
                first_name=None,
                last_name=None,
            )
            session.add(app_user)
            session.flush()
            for role in roles:
                session.add(AppUserRole(app_user_id=app_user.app_user_id, role=role))
            session.add(
                AppSession(
                    app_session_key=session_key,
                    expiration_date=datetime.now(tz=timezone.utc) + timedelta(days=1),
                    app_user_id=app_user.app_user_id,
                )
            )
            session.commit()
            created_user_ids.append(app_user.app_user_id)
        return str(session_key)

    yield _create_user

    with Session(database_engine) as session:
        for app_user_id in created_user_ids:
            session.execute(
                delete(AppSession).where(AppSession.app_user_id == app_user_id)
            )
            session.execute(
                delete(AppUserRole).where(AppUserRole.app_user_id == app_user_id)
            )
            session.execute(delete(AppUser).where(AppUser.app_user_id == app_user_id))
        session.commit()


def _post_with_session_key(client: TestClient, session_key: str) -> httpx.Response:
    """POST to the refresh endpoint as the user owning the session key.

    Args:
        client: Route-level test client.
        session_key: Session cookie value identifying the user.

    Returns:
        The response from the refresh endpoint.
    """
    client.cookies.set("session_key", session_key)
    return client.post(REFRESH_IGDB_GAMES_URL)


def test_returns_401_when_session_cookie_is_missing(client: TestClient):
    """Anonymous requests are rejected without consulting roles.

    Args:
        client: Route-level test client.

    Asserts:
        The endpoint responds with 401 Unauthorized.
    """
    response = client.post(REFRESH_IGDB_GAMES_URL)

    assert response.status_code == 401


def test_returns_401_when_session_cookie_is_unknown(client: TestClient):
    """A cookie that matches no session is treated as anonymous.

    Args:
        client: Route-level test client.

    Asserts:
        The endpoint responds with 401 Unauthorized.
    """
    client.cookies.set("session_key", str(uuid4()))

    response = client.post(REFRESH_IGDB_GAMES_URL)

    assert response.status_code == 401


def test_returns_403_when_user_has_no_roles(
    client: TestClient,
    session_key_factory: Callable[[list[str]], str],
):
    """Authenticated users without any role are forbidden.

    Args:
        client: Route-level test client.
        session_key_factory: Creates a logged-in user with the given roles.

    Asserts:
        The endpoint responds with 403 Forbidden.
    """
    session_key = session_key_factory([])

    response = _post_with_session_key(client, session_key)

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized"}


def test_returns_403_when_role_lacks_permission_on_resource(
    client: TestClient,
    session_key_factory: Callable[[list[str]], str],
):
    """A role that exists but holds no igdb_games permission is forbidden.

    Args:
        client: Route-level test client.
        session_key_factory: Creates a logged-in user with the given roles.

    Asserts:
        The endpoint responds with 403 Forbidden.
    """
    session_key = session_key_factory(["user"])

    response = _post_with_session_key(client, session_key)

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized"}


def test_returns_202_when_user_can_write_igdb_games(
    client: TestClient,
    session_key_factory: Callable[[list[str]], str],
    mocker: MockerFixture,
):
    """Admins pass the authorization check and the job is scheduled.

    Args:
        client: Route-level test client.
        session_key_factory: Creates a logged-in user with the given roles.
        mocker: pytest-mock fixture used to stub the background job.

    Asserts:
        The endpoint responds with 202 and a started status payload.
    """
    mocker.patch("app.features.admin.refresh_igdb_games_handler.RefreshIgdbGamesJob")
    session_key = session_key_factory(["admin"])

    response = _post_with_session_key(client, session_key)

    assert response.status_code == 202
    assert response.json() == {"status": "started"}
