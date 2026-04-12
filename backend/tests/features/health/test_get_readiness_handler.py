from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.database.engine import create_connection_url, create_db_session
from app.features.health.get_readiness_handler import (
    GetReadinessHandler,
    GetReadinessResponse,
)
from app.settings import get_settings


def test_handle_returns_ready_when_database_query_succeeds(db_session: Session):
    handler = GetReadinessHandler(db_session)

    actual = handler.handle()

    assert actual == GetReadinessResponse(message="Database is ready.")


def test_handle_raises_500_when_database_query_fails():
    bad_database_settings = get_settings().model_copy(
        update={"db_database": f"BacklogBossTestMissing_{uuid4().hex}"}
    )
    bad_engine: Engine = create_engine(create_connection_url(bad_database_settings))

    try:
        with create_db_session(bad_engine) as bad_session:
            handler = GetReadinessHandler(bad_session)

            with pytest.raises(HTTPException) as exc_info:
                handler.handle()
    finally:
        bad_engine.dispose()

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "Database is not ready."
