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

    backlogs: Mapped[list["Backlog"]] = relationship(
        "Backlog", back_populates="app_user"
    )


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


class Game(Base):
    __tablename__ = "Game"

    game_id: Mapped[int] = mapped_column("GameId", primary_key=True)
    title: Mapped[str] = mapped_column("Title", String(255))
    steam_id: Mapped[int] = mapped_column("SteamGameId")
    igdb_id: Mapped[int] = mapped_column("IgdbGameId")

    def __str__(self):
        return f"Game id: {self.game_id}, title: {self.title}, steam_id: {self.steam_id}, igdb_id: {self.igdb_id}"

    def __repr__(self) -> str:
        return self.__str__()


class Backlog(Base):
    __tablename__ = "Backlog"

    backlog_id: Mapped[int] = mapped_column("BacklogId", primary_key=True)
    app_user_id: Mapped[int] = mapped_column(
        "AppUserId", ForeignKey("AppUser.AppUserId")
    )

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="backlogs")
    backlog_games: Mapped[list["BacklogGame"]] = relationship(
        "BacklogGame", back_populates="backlog"
    )


class BacklogGame(Base):
    __tablename__ = "BacklogGame"

    backlog_game_id: Mapped[int] = mapped_column("BacklogGameId", primary_key=True)
    backlog_id: Mapped[int] = mapped_column(
        "BacklogId", ForeignKey("Backlog.BacklogId")
    )
    game_id: Mapped[int] = mapped_column("GameId", ForeignKey("Game.GameId"))

    backlog: Mapped["Backlog"] = relationship("Backlog", back_populates="backlog_games")
    game: Mapped["Game"] = relationship("Game")
