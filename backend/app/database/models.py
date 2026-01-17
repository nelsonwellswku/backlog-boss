from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.mssql import DATETIMEOFFSET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AppUser(Base):
    __tablename__ = "AppUser"

    app_user_id: Mapped[int] = mapped_column("AppUserId", primary_key=True)
    steam_id: Mapped[str] = mapped_column("SteamId", String(17))
    persona_name: Mapped[str] = mapped_column("PersonaName", String(32))
    first_name: Mapped[Optional[str]] = mapped_column("FirstName", String(20))
    last_name: Mapped[Optional[str]] = mapped_column("LastName", String(20))


class AppSession(Base):
    __tablename__ = "AppSession"

    app_session_id: Mapped[int] = mapped_column(
        "AppSessionId", BigInteger, primary_key=True
    )
    app_session_key: Mapped[UUID] = mapped_column(
        "AppSessionKey", server_default="newsequentialid()"
    )
    expiration_date: Mapped[datetime] = mapped_column("ExpirationDate", DATETIMEOFFSET)

    app_user_id: Mapped[int] = mapped_column(
        "AppUserId", ForeignKey("AppUser.AppUserId")
    )
    app_user: Mapped[AppUser] = relationship()
