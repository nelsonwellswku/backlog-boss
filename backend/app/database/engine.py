from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from app.settings import get_settings

settings = get_settings()


connection_url = URL.create(
    "mssql+pyodbc",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=1433,
    database="BacklogBoss",
    query={"driver": "ODBC Driver 18 for SQL Server", "TrustServerCertificate": "yes"},
)

db_engine = create_engine(connection_url)


def get_db_session():
    with Session(db_engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_db_session)]
