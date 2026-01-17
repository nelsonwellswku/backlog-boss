from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated, TypeAlias

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import AppSession, AppUser


@dataclass
class User:
    app_user_id: int
    steam_id: str
    persona_name: str
    first_name: str | None
    last_name: str | None


def get_current_user(request: Request, db: DbSession):
    session_key = request.cookies.get("session_key")

    if session_key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    now = datetime.now(tz=timezone.utc)
    stmt = (
        select(AppSession)
        .join(AppUser)
        .where(AppSession.app_session_key == session_key)
        .where(AppSession.expiration_date > now)
    )
    app_session = db.scalars(stmt).one_or_none()
    if app_session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    app_user = app_session.app_user

    return User(
        app_user_id=app_user.app_user_id,
        steam_id=app_user.steam_id,
        persona_name=app_user.persona_name,
        first_name=app_user.first_name,
        last_name=app_user.last_name,
    )


CurrentUser: TypeAlias = Annotated[User, Depends(get_current_user)]
