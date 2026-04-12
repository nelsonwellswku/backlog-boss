from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import Session, sessionmaker

from app.settings import Settings, get_settings


def create_connection_url(settings: Settings) -> URL:
    return URL.create(
        "mssql+pyodbc",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_database,
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "TrustServerCertificate": "yes",
        },
    )


@lru_cache
def get_db_engine() -> Engine:
    return create_engine(create_connection_url(get_settings()))


@lru_cache
def get_db_session_factory() -> sessionmaker[Session]:
    return sessionmaker(get_db_engine())


def reset_db_engine() -> None:
    if get_db_engine.cache_info().currsize:
        get_db_engine().dispose()
    get_db_engine.cache_clear()
    get_db_session_factory.cache_clear()


def create_db_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine)


@contextmanager
def create_db_session(engine: Engine | None = None) -> Iterator[Session]:
    session_factory = (
        get_db_session_factory()
        if engine is None
        else create_db_session_factory(engine)
    )
    with session_factory() as session:
        yield session


def get_db_session():
    with create_db_session() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db_session)]
