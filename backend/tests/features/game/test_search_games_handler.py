import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AppUser, IgdbExternalGame, IgdbGame, IgdbGameTimeToBeat
from app.features.auth.get_current_user import User
from app.features.game.search_games_handler import SearchGamesHandler
from app.infrastructure.igdb_client import (
    ExternalGameResponse,
    IgdbGameResponse,
    TimeToBeatResponse,
)


def _create_current_user(db_session: Session) -> User:
    app_user = AppUser(
        steam_id="76561198000000000",
        persona_name="Test Persona",
        first_name="Test",
        last_name="User",
    )
    db_session.add(app_user)
    db_session.flush()

    return User(
        app_user_id=app_user.app_user_id,
        steam_id=app_user.steam_id,
        persona_name=app_user.persona_name,
        first_name=app_user.first_name,
        last_name=app_user.last_name,
    )


def test_handle_returns_database_matches_without_calling_igdb(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_current_user(db_session)
    steam_match = IgdbGame(igdb_game_id=10, name="Portal 2", total_rating=95.0)
    steam_match.time_to_beat = IgdbGameTimeToBeat(
        igdb_game_time_to_beat_id=101,
        igdb_game_id=10,
        normally=28800,
    )
    steam_match.external_games.append(
        IgdbExternalGame(
            igdb_external_game_id=201,
            uid=620,
            igdb_external_game_source_id=1,
        )
    )
    non_steam_match = IgdbGame(
        igdb_game_id=11, name="Portal Stories VR", total_rating=70.0
    )
    non_steam_match.external_games.append(
        IgdbExternalGame(
            igdb_external_game_id=202,
            uid=777,
            igdb_external_game_source_id=5,
        )
    )
    db_session.add_all([steam_match, non_steam_match])
    db_session.commit()

    igdb_client = mocker.Mock()

    actual = SearchGamesHandler(db_session, igdb_client).handle("portal")

    assert [(row.game_id, row.title, row.time_to_beat) for row in actual.games] == [
        (10, "Portal 2", 28800),
    ]
    igdb_client.search_games_by_name.assert_not_called()


def test_handle_fetches_from_igdb_persists_results_and_returns_them(
    db_session: Session,
    mocker: MockerFixture,
):
    _create_current_user(db_session)
    igdb_client = mocker.Mock()
    igdb_client.search_games_by_name.return_value = [
        IgdbGameResponse(
            id=44,
            name="Hades II",
            total_rating=93.5,
            external_games=[
                ExternalGameResponse(
                    id=301,
                    game=44,
                    uid="1145350",
                    external_game_source=1,
                )
            ],
            time_to_beat=TimeToBeatResponse(id=401, game_id=44, normally=43200),
        ),
        IgdbGameResponse(
            id=45,
            name="Hades Tactics",
            total_rating=None,
            external_games=[
                ExternalGameResponse(
                    id=302,
                    game=45,
                    uid="1145351",
                    external_game_source=1,
                )
            ],
            time_to_beat=None,
        ),
    ]

    actual = SearchGamesHandler(db_session, igdb_client).handle("hades")

    assert [(row.game_id, row.title, row.time_to_beat) for row in actual.games] == [
        (44, "Hades II", 43200),
        (45, "Hades Tactics", None),
    ]
    igdb_client.search_games_by_name.assert_called_once_with("hades")

    persisted_games = db_session.scalars(
        select(IgdbGame).where(IgdbGame.igdb_game_id.in_([44, 45]))
    ).all()
    persisted_external_uids = db_session.scalars(
        select(IgdbExternalGame.uid).where(IgdbExternalGame.igdb_game_id.in_([44, 45]))
    ).all()

    assert sorted(game.name for game in persisted_games) == [
        "Hades II",
        "Hades Tactics",
    ]
    assert persisted_external_uids == [1145350, 1145351]


def test_handle_raises_for_blank_queries(
    db_session: Session,
    mocker: MockerFixture,
):
    handler = SearchGamesHandler(db_session, mocker.Mock())

    with pytest.raises(HTTPException) as exc_info:
        handler.handle("   ")

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Search query must not be blank."
