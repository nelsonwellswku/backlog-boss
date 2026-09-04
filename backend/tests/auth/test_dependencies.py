import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import requires_authorization
from app.auth.permissions import Permission, Resource
from app.database.models import AppUser, AppUserRole
from app.features.auth.get_current_user import User


def _create_user_with_roles(
    db_session: Session, roles: list[str]
) -> tuple[AppUser, User]:
    app_user = AppUser(
        steam_id="76561198000000000",
        persona_name="Test Persona",
        first_name="Test",
        last_name="User",
    )
    db_session.add(app_user)
    db_session.flush()

    for role in roles:
        db_session.add(AppUserRole(app_user_id=app_user.app_user_id, role=role))
    db_session.flush()

    user = User(
        app_user_id=app_user.app_user_id,
        steam_id=app_user.steam_id,
        persona_name=app_user.persona_name,
        first_name=app_user.first_name,
        last_name=app_user.last_name,
    )
    return app_user, user


def test_returns_user_when_has_required_permission(
    db_session: Session,
):
    _, user = _create_user_with_roles(db_session, ["admin"])
    dep = requires_authorization(Permission.WRITE, Resource.IGDB_GAMES)

    result = asyncio.run(dep.dependency(current_user=user, db=db_session))

    assert result == user


def test_raises_403_when_role_has_no_matching_permission(
    db_session: Session,
):
    _, user = _create_user_with_roles(db_session, ["user"])
    dep = requires_authorization(Permission.WRITE, Resource.IGDB_GAMES)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(dep.dependency(current_user=user, db=db_session))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Not authorized"


def test_raises_403_when_role_exists_but_lacks_permission_on_resource(
    db_session: Session,
):
    _, user = _create_user_with_roles(db_session, ["user"])
    dep = requires_authorization(Permission.READ, Resource.IGDB_GAMES)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(dep.dependency(current_user=user, db=db_session))

    assert exc_info.value.status_code == 403


def test_raises_403_when_user_has_no_roles(
    db_session: Session,
):
    _, user = _create_user_with_roles(db_session, [])
    dep = requires_authorization(Permission.READ, Resource.IGDB_GAMES)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(dep.dependency(current_user=user, db=db_session))

    assert exc_info.value.status_code == 403
