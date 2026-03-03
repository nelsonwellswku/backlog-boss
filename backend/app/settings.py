from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    db_host: str
    db_user: str
    db_password: str
    db_database: str

    twitch_client_id: str
    twitch_client_secret: str
    steam_api_key: str

    base_url: str = "http://localhost:5173"

    @field_validator("base_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


@lru_cache
def get_settings():
    # type is ignored because the constructor "requires" each fields to be passed in
    # but those values are automatically provided via env vars
    return Settings()  # type: ignore


AppSettings = Annotated[Settings, Depends(get_settings)]
