from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import AppUserRole
from app.features.auth.get_current_user import RequiredCurrentUser, User

from .roles import ROLES


def requires_authorization(permission: str, resource: str) -> Any:
    """Dependency factory that checks if the current user has the required permission.

    Args:
        permission: The permission to check (e.g., Permission.READ, Permission.WRITE).
        resource: The resource to check against (e.g., Resource.IGDB_GAMES).

    Returns:
        A FastAPI dependency that returns the current user if authorized,
        or raises HTTP 403 Forbidden.
    """

    async def _check(current_user: RequiredCurrentUser, db: DbSession) -> User:
        stmt = select(AppUserRole.role).where(
            AppUserRole.app_user_id == current_user.app_user_id
        )
        roles = set(db.scalars(stmt).all())

        for role in roles:
            role_perms = ROLES.get(role, {}).get(resource, [])
            if permission in role_perms:
                return current_user

        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    return Depends(_check)
