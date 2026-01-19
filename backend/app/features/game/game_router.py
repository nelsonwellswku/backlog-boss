from fastapi import APIRouter
from sqlalchemy import select

from app.database.engine import DbSession
from app.database.models import Game
from app.features.auth.get_current_user import CurrentUser
from app.features.game.igdb_client import IgdbClientDep
from app.features.game.steam_client import SteamClientDep

game_router = APIRouter()


# api endpoint that
# 1. fetches users owned games from steam
# 2. fetches all of the games' details from igdb
# 3. adds them to the game table in the database
@game_router.post("/api/game/create_my_games")
def create_my_games(
    db: DbSession,
    steam: SteamClientDep,
    current_user: CurrentUser,
    igdb_client: IgdbClientDep,
):
    # find the games the user owns but are not already in the database
    owned_games = steam.get_owned_games(current_user.steam_id)[:1]
    owned_game_ids = set([game.steam_game_id for game in owned_games])
    stmt = select(Game).where(
        Game.steam_id.not_in([game.steam_game_id for game in owned_games])
    )
    games_in_the_database_that_are_owned = db.scalars(stmt).all()
    games_in_the_database_that_are_owned_ids = set([game.steam_id for game in games_in_the_database_that_are_owned])
    print("owned game ids", owned_game_ids)
    print("games in db ids", games_in_the_database_that_are_owned_ids)
    game_ids_to_insert = games_in_the_database_that_are_owned_ids - owned_game_ids

    # fetch the games to insert from igdb and save them to the database
    igdb_games = igdb_client.get_games(list(game_ids_to_insert), len(game_ids_to_insert))
    games_to_insert = [Game(title=game.title, igdb_id=game.igdb_game_id, steam_id=game.steam_game_id) for game in igdb_games]
    print(games_to_insert)
    db.add_all(games_to_insert)
    db.commit()

    return None
