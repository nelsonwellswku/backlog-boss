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


class Backlog(Base):
    __tablename__ = "Backlog"

    backlog_id: Mapped[int] = mapped_column("BacklogId", primary_key=True)
    app_user_id: Mapped[int] = mapped_column(
        "AppUserId", ForeignKey("AppUser.AppUserId")
    )

    app_user: Mapped["AppUser"] = relationship("AppUser", back_populates="backlogs")
    backlog_games: Mapped[list["BacklogGame"]] = relationship(
        "BacklogGame", back_populates="backlog", lazy="raise"
    )


class BacklogGame(Base):
    __tablename__ = "BacklogGame"

    backlog_game_id: Mapped[int] = mapped_column("BacklogGameId", primary_key=True)
    backlog_id: Mapped[int] = mapped_column(
        "BacklogId", ForeignKey("Backlog.BacklogId")
    )
    igdb_game_id: Mapped[int] = mapped_column("IgdbGameId", ForeignKey("IgdbGame.Id"))

    backlog: Mapped["Backlog"] = relationship("Backlog", back_populates="backlog_games")
    igdb_game: Mapped["IgdbGame"] = relationship("IgdbGame", lazy="raise")


class IgdbGame(Base):
    __tablename__ = "IgdbGame"

    igdb_game_id: Mapped[int] = mapped_column(
        "Id", primary_key=True, autoincrement=False
    )
    name: Mapped[str] = mapped_column("Name", String(255))
    total_rating: Mapped[Optional[float]] = mapped_column("TotalRating")

    external_games: Mapped[list["IgdbExternalGame"]] = relationship(
        "IgdbExternalGame", back_populates="igdb_game"
    )
    time_to_beat: Mapped[Optional["IgdbGameTimeToBeat"]] = relationship(
        "IgdbGameTimeToBeat", back_populates="igdb_game", lazy="raise"
    )


class IgdbExternalGame(Base):
    __tablename__ = "IgdbExternalGame"

    igdb_external_game_id: Mapped[int] = mapped_column(
        "Id", primary_key=True, autoincrement=False
    )
    uid: Mapped[int] = mapped_column("Uid")
    igdb_game_id: Mapped[int] = mapped_column("IgdbGameId", ForeignKey("IgdbGame.Id"))
    igdb_external_game_source_id: Mapped[int] = mapped_column(
        "IgdbExternalGameSourceId", ForeignKey("IgdbExternalGameSource.Id")
    )

    igdb_game: Mapped["IgdbGame"] = relationship(
        "IgdbGame",
        back_populates="external_games",
    )
    source: Mapped["IgdbExternalGameSource"] = relationship("IgdbExternalGameSource")


class IgdbExternalGameSource(Base):
    __tablename__ = "IgdbExternalGameSource"

    igdb_external_game_source_id: Mapped[int] = mapped_column(
        "Id", primary_key=True, autoincrement=False
    )
    name: Mapped[str] = mapped_column("Name", String(32))


class IgdbGameTimeToBeat(Base):
    __tablename__ = "IgdbGameTimeToBeat"

    igdb_game_time_to_beat_id: Mapped[int] = mapped_column(
        "Id", primary_key=True, autoincrement=False
    )
    normally: Mapped[Optional[int]] = mapped_column("Normally")
    igdb_game_id: Mapped[int] = mapped_column("IgdbGameId", ForeignKey("IgdbGame.Id"))

    igdb_game: Mapped["IgdbGame"] = relationship(
        "IgdbGame", back_populates="time_to_beat"
    )
