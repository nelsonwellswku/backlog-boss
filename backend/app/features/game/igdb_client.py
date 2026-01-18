import json
from typing import Annotated, TypeAlias

from expiring_dict import ExpiringDict
from fastapi import Depends
from httpx import QueryParams
from igdb.wrapper import IGDBWrapper

from app.http_client import HttpClient
from app.settings import AppSettings

access_token_cache = ExpiringDict()
access_token_key = "access_token"


def get_valid_twitch_access_token(settings: AppSettings, http_client: HttpClient):
    if access_token_key not in access_token_cache:
        query_params: QueryParams = QueryParams(
            client_id=settings.twitch_client_id,
            client_secret=settings.twitch_client_secret,
            grant_type="client_credentials",
        )
        response = http_client.post(
            "https://id.twitch.tv/oauth2/token", params=query_params
        )
        response_json = response.json()
        access_token_cache.ttl(
            access_token_key, response_json["access_token"], response_json["expires_in"]
        )

    return access_token_cache[access_token_key]


def get_igdb_wrapper(
    settings: AppSettings, access_token=Depends(get_valid_twitch_access_token)
):
    return IGDBWrapper(settings.twitch_client_id, access_token)


class IgdbClientX:
    def __init__(self, igdb_wrapper=Depends(get_igdb_wrapper)):
        self.igdb_wrapper = igdb_wrapper

    def get_external_games(self):
        bytes = self.igdb_wrapper.api_request(
            "external_games",
            "fields id, game, name; where external_game_source = 1; offset 0; limit 10;",
        )
        games = json.loads(bytes)
        return games

    def get_games(self):
        pass


IgdbClient: TypeAlias = Annotated[IgdbClientX, Depends(IgdbClientX)]
