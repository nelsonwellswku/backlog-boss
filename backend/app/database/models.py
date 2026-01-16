from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AppUser(Base):
    __tablename__ = "AppUser"

    app_user_id: Mapped[int] = mapped_column("appUserId", primary_key=True)
    steam_id: Mapped[str] = mapped_column("steamId", String(17))
    persona_name: Mapped[str] = mapped_column("personaName", String(32))
    first_name: Mapped[Optional[str]] = mapped_column("firstName", String(20))
    last_name: Mapped[Optional[str]] = mapped_column("lastName", String(20))
