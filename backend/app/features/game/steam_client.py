from dataclasses import dataclass
from typing import Annotated, TypeAlias

from fastapi import Depends
from steam_web_api import Steam

from app.settings import AppSettings


def get_steam(settings: AppSettings) -> Steam:
    return Steam(settings.steam_api_key)


@dataclass
class SteamGame:
    steam_game_id: int


class SteamClient:
    def __init__(self, steam: Steam = Depends(get_steam)):
        self.steam = steam

    def get_owned_games(self, steam_id: str):
        owned_games_response = self.steam.users.get_owned_games(
            steam_id, include_free_games=False, include_appinfo=False
        )
        return [SteamGame(game["appid"]) for game in owned_games_response["games"]]


SteamClientDep: TypeAlias = Annotated[SteamClient, Depends(SteamClient)]
