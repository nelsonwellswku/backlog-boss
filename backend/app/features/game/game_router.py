from fastapi import APIRouter

from app.database.engine import DbSession
from app.features.auth.get_current_user import CurrentUser
from app.features.game.igdb_client import IgdbClient
from app.features.game.steam_client import SteamClient

game_router = APIRouter()


# api endpoint that
# 1. fetches users owned games from steam
# 2. fetches all of the games' details from igdb
# 3. adds them to the game table in the database
# 4. adds them to the users owned games in the database
@game_router.post("/api/game/create_my_games")
def create_my_games(
    db: DbSession,
    steam: SteamClient,
    current_user: CurrentUser,
    igdb_client: IgdbClient,
):
    owned_games = steam.users.get_owned_games(
        current_user.steam_id, include_appinfo=False, includ_free_games=False
    )
    igdb_games = igdb_client.get_external_games()
    return igdb_games
