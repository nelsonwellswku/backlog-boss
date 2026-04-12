from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AppUser


TEST_STEAM_ID = "76561198000000042"


def _create_app_user() -> AppUser:
    return AppUser(
        steam_id=TEST_STEAM_ID,
        persona_name="Isolated Persona",
        first_name=None,
        last_name=None,
    )


def test_database_starts_from_clean_baseline(db_session: Session):
    db_session.add(_create_app_user())
    db_session.commit()

    actual = db_session.scalars(
        select(AppUser).where(AppUser.steam_id == TEST_STEAM_ID)
    ).one()

    assert actual.persona_name == "Isolated Persona"


def test_database_is_reset_between_tests(db_session: Session):
    assert (
        db_session.scalars(
            select(AppUser).where(AppUser.steam_id == TEST_STEAM_ID)
        ).one_or_none()
        is None
    )

    db_session.add(_create_app_user())
    db_session.commit()
