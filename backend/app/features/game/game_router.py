from fastapi import APIRouter, Response
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import Backlog, BacklogGame, Game
from app.features.auth.get_current_user import CurrentUser
from app.features.game.igdb_client import IgdbClientDep
from app.features.game.steam_client import SteamClientDep

game_router = APIRouter()


# api endpoint that
# 1. fetches users owned games from steam
# 2. fetches all of the games' details from igdb
# 3. adds them to the game table in the database
# 4. creates the user's backlog
# 5. adds their owned games to the backlog
@game_router.post("/api/game/create_my_backlog")
def create_my_backlog(
    db: DbSession,
    steam: SteamClientDep,
    current_user: CurrentUser,
    igdb_client: IgdbClientDep,
):
    # if the user already has a backlog, return early
    # adding / removing items from the backlog can happen elsewhere
    stmt = select(Backlog).where(Backlog.app_user_id == current_user.app_user_id)
    backlog = db.scalars(stmt).one_or_none()
    if backlog:
        return Response()

    backlog = Backlog(app_user_id=current_user.app_user_id)

    # find the games the user owns but are not already in the database
    owned_games = steam.get_owned_games(current_user.steam_id)
    owned_game_steam_ids = set([game.steam_game_id for game in owned_games])

    # query for games already in the database with these steam_ids
    stmt = select(Game.steam_id).where(Game.steam_id.in_(owned_game_steam_ids))
    games_in_db = db.scalars(stmt).all()
    games_in_db_ids = set(games_in_db)

    game_ids_to_insert = owned_game_steam_ids - games_in_db_ids

    # fetch the games to insert from igdb and save them to the database
    igdb_games = igdb_client.get_games(game_ids_to_insert, len(game_ids_to_insert))

    # we need to double check that the games we get back are not already in the db
    # this is because when querying igdb for steam games, igdb will sometimes return
    # two steam ids for a singular igdb id - one of these we'll _never_ insert
    stmt = select(Game.igdb_id).where(
        Game.igdb_id.in_([game.igdb_game_id for game in igdb_games])
    )
    igdb_ids_to_preclude_from_insert = set(db.scalars(stmt).all())

    games_to_insert = [
        Game(title=game.title, igdb_id=game.igdb_game_id, steam_id=game.steam_game_id)
        for game in igdb_games
        if game.igdb_game_id not in igdb_ids_to_preclude_from_insert
    ]

    db.add_all(games_to_insert)
    db.flush()

    # re-query owned games by steam id in case a subset of the user's owned games
    # already existed in the database when we inserted new Game records above
    stmt = select(Game).where(Game.steam_id.in_(owned_game_steam_ids))
    games_to_add_to_backlog = db.scalars(stmt).all()

    backlog_games = [
        BacklogGame(backlog=backlog, game=game) for game in games_to_add_to_backlog
    ]
    db.add(backlog)
    db.add_all(backlog_games)

    db.commit()

    return Response()
