import json
from dataclasses import dataclass
from typing import Annotated, TypeAlias, TypedDict

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


class IgdbGameDict(TypedDict):
    id: int
    name: str


class IgdbExternalGameDict(TypedDict):
    uid: str
    game: IgdbGameDict


@dataclass
class IgdbGame:
    igdb_game_id: int
    steam_game_id: int
    title: str


class IgdbClient:
    def __init__(self, igdb_wrapper: IGDBWrapper = Depends(get_igdb_wrapper)):
        self.igdb_wrapper = igdb_wrapper

    def get_games(self, steam_ids: set[int], limit: int) -> list[IgdbGame]:
        formatted_steam_ids = ", ".join([str(id) for id in steam_ids])
        endpoint = "external_games"
        query = f"""
            fields uid, game.id, game.name;
            where external_game_source = 1 & uid = ({formatted_steam_ids});
            offset 0;
            limit {limit};
        """
        bytes = self.igdb_wrapper.api_request(endpoint, query)
        games_json: list[IgdbExternalGameDict] = json.loads(bytes)
        
        # Filter out any malformed responses that don't have the required fields
        games = [
            IgdbGame(v["game"]["id"], int(v["uid"]), v["game"]["name"])
            for v in games_json
            if "game" in v and "id" in v["game"] and "name" in v["game"] and "uid" in v
        ]

        # dedup the list - this is required because a single igdb game can
        # be related to multiple steam games. for example,
        # mass effect 2 (2010 edition) - igdb id 74, steam id 2362420
        # mass effect 2 - igdb id 74, steam id 24980
        games.sort(key=lambda g: (g.steam_game_id, g.igdb_game_id))
        igdb_games_seen = set()
        games = [
            g
            for g in games
            if g.igdb_game_id not in igdb_games_seen
            and not igdb_games_seen.add(g.igdb_game_id)
        ]

        return games


IgdbClientDep: TypeAlias = Annotated[IgdbClient, Depends(IgdbClient)]
