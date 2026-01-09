from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    twitch_client_id: str
    twitch_client_secret: str
    steam_api_key: str


@lru_cache
def get_settings():
    # type is ignored because the constructor "requires" each fields to be passed in
    # but those values are automatically provided via env vars
    return Settings()  # type: ignore


AppSettings = Annotated[Settings, Depends(get_settings)]
