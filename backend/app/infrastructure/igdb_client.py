import json
from typing import Annotated, TypeAlias

from expiring_dict import ExpiringDict
from fastapi import Depends
from httpx import QueryParams
from igdb.wrapper import IGDBWrapper
from pydantic import BaseModel

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


class ExternalGameSource(BaseModel):
    id: int


class ExternalGame(BaseModel):
    id: int
    uid: str
    external_game_source: ExternalGameSource


class IgdbGameResponse(BaseModel):
    id: int
    name: str
    total_rating: float | None = None
    external_games: list[ExternalGame] = []
    time_to_beat: "TimeToBeatResponse | None" = None


class TimeToBeatResponse(BaseModel):
    id: int
    game_id: int
    normally: int | None = None


class IgdbClient:
    def __init__(self, igdb_wrapper: IGDBWrapper = Depends(get_igdb_wrapper)):
        self.igdb_wrapper = igdb_wrapper

    def get_games(self, steam_ids: set[int]) -> list[IgdbGameResponse]:
        formatted_steam_ids = ", ".join([str(id) for id in steam_ids])
        endpoint = "games"
        query = f"""
            fields id, name, total_rating, external_games.uid, external_games.external_game_source.id;
            where external_games.uid = ({formatted_steam_ids}) & external_games.external_game_source = (1);
            offset 0;
            limit {len(steam_ids)};
        """
        bytes = self.igdb_wrapper.api_request(endpoint, query)
        games_json = json.loads(bytes)
        if not games_json:
            return []

        games = [IgdbGameResponse.model_validate(game) for game in games_json]
        for g in games:
            external_games = [
                eg for eg in g.external_games if eg.external_game_source.id == 1
            ]
            g.external_games = external_games

        game_time_to_beats = self.get_game_time_to_beats([g.id for g in games])
        igdb_game_id_to_game_time_to_beat = {
            gttb.game_id: gttb for gttb in game_time_to_beats
        }

        for g in games:
            time_to_beat = igdb_game_id_to_game_time_to_beat.get(g.id, None)
            if time_to_beat:
                g.time_to_beat = time_to_beat

        return games

    def get_game_time_to_beats(self, igdb_game_ids: list[int]):
        formatted_game_ids = ", ".join([str(id) for id in igdb_game_ids])
        endpoint = "game_time_to_beats"
        query = f"""
            fields id, game_id, normally;
            where game_id = ({formatted_game_ids});
            offset 0;
            limit {len(igdb_game_ids)};
        """

        response_bytes = self.igdb_wrapper.api_request(endpoint, query)
        response_json = json.loads(response_bytes)
        game_time_to_beats = [
            TimeToBeatResponse.model_validate(ttb) for ttb in response_json
        ]

        return game_time_to_beats


IgdbClientDep: TypeAlias = Annotated[IgdbClient, Depends(IgdbClient)]
