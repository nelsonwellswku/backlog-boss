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


@dataclass
class SteamUserDetails:
    persona_name: str
    real_name: str | None


class SteamClient:
    def __init__(self, steam: "SteamDep"):
        self.steam = steam

    def get_owned_games(self, steam_id: str) -> list[SteamGame]:
        owned_games_response = self.steam.users.get_owned_games(
            steam_id, includ_free_games=False, include_appinfo=False
        )
        return [SteamGame(game["appid"]) for game in owned_games_response["games"]]

    def get_user_details(self, steam_id: str) -> SteamUserDetails:
        user_details = self.steam.users.get_user_details(steam_id)
        player = user_details["player"]
        return SteamUserDetails(
            persona_name=player["personaname"],
            real_name=player.get("realname"),
        )


SteamDep: TypeAlias = Annotated[Steam, Depends(get_steam)]
SteamClientDep: TypeAlias = Annotated[SteamClient, Depends(SteamClient)]
