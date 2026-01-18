from typing import Annotated, TypeAlias

from fastapi import Depends
from steam_web_api import Steam

from app.settings import AppSettings


def get_steam_client(settings: AppSettings) -> Steam:
    return Steam(settings.steam_api_key)


SteamClient: TypeAlias = Annotated[Steam, Depends(get_steam_client)]
