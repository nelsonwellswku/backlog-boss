from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AppUser,
    Backlog,
    BacklogGame,
    IgdbExternalGame,
    IgdbGame,
    IgdbGameTimeToBeat,
)
from app.features.auth.get_current_user import User
from app.features.user.create_my_backlog_handler import CreateMyBacklogHandler
from app.infrastructure.igdb_client import (
    ExternalGameResponse,
    IgdbGameResponse,
    TimeToBeatResponse,
)
from app.infrastructure.steam_client import SteamGame


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


def test_handle_returns_existing_backlog_without_fetching_external_data(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    backlog = Backlog(app_user_id=current_user.app_user_id)
    db_session.add(backlog)
    db_session.commit()

    steam_client = mocker.Mock()
    igdb_client = mocker.Mock()
    handler = CreateMyBacklogHandler(db_session, steam_client, current_user, igdb_client)

    actual = handler.handle()

    assert actual.backlog_id == backlog.backlog_id
    steam_client.get_owned_games.assert_not_called()
    igdb_client.get_games_by_steam_id.assert_not_called()


def test_handle_creates_backlog_and_adds_only_games_with_rating_and_time_to_beat(
    db_session: Session,
    mocker: MockerFixture,
):
    current_user = _create_current_user(db_session)
    existing_game = IgdbGame(igdb_game_id=1, name="Existing Game", total_rating=88.0)
    existing_game.time_to_beat = IgdbGameTimeToBeat(
        igdb_game_time_to_beat_id=101,
        igdb_game_id=1,
        normally=3600,
    )
    existing_game.external_games.append(
        IgdbExternalGame(
            igdb_external_game_id=1001,
            uid=111,
            igdb_external_game_source_id=1,
        )
    )
    db_session.add(existing_game)
    db_session.flush()

    steam_client = mocker.Mock()
    steam_client.get_owned_games.return_value = [
        SteamGame(steam_game_id=111),
        SteamGame(steam_game_id=222),
        SteamGame(steam_game_id=333),
    ]
    igdb_client = mocker.Mock()
    igdb_client.get_games_by_steam_id.return_value = [
        IgdbGameResponse(
            id=2,
            name="New Complete Game",
            total_rating=91.0,
            external_games=[
                ExternalGameResponse(id=2001, game=2, uid="222", external_game_source=1),
                ExternalGameResponse(
                    id=2002,
                    game=2,
                    uid="222,223",
                    external_game_source=1,
                ),
            ],
            time_to_beat=TimeToBeatResponse(id=3001, game_id=2, normally=7200),
        ),
        IgdbGameResponse(
            id=3,
            name="New Incomplete Game",
            total_rating=63.0,
            external_games=[
                ExternalGameResponse(id=2003, game=3, uid="333", external_game_source=1)
            ],
            time_to_beat=None,
        ),
    ]
    handler = CreateMyBacklogHandler(db_session, steam_client, current_user, igdb_client)

    actual = handler.handle()

    backlog = db_session.scalars(
        select(Backlog).where(Backlog.backlog_id == actual.backlog_id)
    ).one()
    backlog_game_ids = db_session.scalars(
        select(BacklogGame.igdb_game_id).where(BacklogGame.backlog_id == backlog.backlog_id)
    ).all()
    inserted_external_uids = db_session.scalars(
        select(IgdbExternalGame.uid).where(IgdbExternalGame.igdb_game_id == 2)
    ).all()

    assert backlog.app_user_id == current_user.app_user_id
    assert set(backlog_game_ids) == {1, 2}
    assert inserted_external_uids == [222]
    steam_client.get_owned_games.assert_called_once_with(current_user.steam_id)
    igdb_client.get_games_by_steam_id.assert_called_once_with({222, 333})

