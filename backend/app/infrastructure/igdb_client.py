import json
from itertools import groupby
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


class IgdbGameResponse(BaseModel):
    id: int
    name: str
    total_rating: float | None = None
    external_games: list["ExternalGameResponse"] = []
    time_to_beat: "TimeToBeatResponse | None" = None


class ExternalGameResponse(BaseModel):
    id: int
    game: int
    uid: str
    external_game_source: int


class TimeToBeatResponse(BaseModel):
    id: int
    game_id: int
    normally: int | None = None


class IgdbClient:
    def __init__(self, igdb_wrapper: IGDBWrapper = Depends(get_igdb_wrapper)):
        self.igdb_wrapper = igdb_wrapper

    def _format_ids(self, ids: list[int]):
        return ", ".join([str(id) for id in ids])

    def get_games(self, steam_ids: set[int]) -> list[IgdbGameResponse]:
        formatted_steam_ids = ", ".join([str(id) for id in steam_ids])
        endpoint = "games"
        query = f"""
            fields id, name, total_rating;
            where external_games.uid = ({formatted_steam_ids}) & external_games.external_game_source = (1);
            offset 0;
            limit {len(steam_ids)};
        """
        bytes = self.igdb_wrapper.api_request(endpoint, query)
        games_json = json.loads(bytes)
        if not games_json:
            return []

        games = [IgdbGameResponse.model_validate(game) for game in games_json]
        game_ids = [g.id for g in games]
        game_id_to_game = {g.id: g for g in games}

        external_games = self.get_external_games(game_ids)
        external_games.sort(key=lambda x: x.game)
        grouped_external_games = groupby(external_games, lambda x: x.game)

        game_time_to_beats = self.get_game_time_to_beats([g.id for g in games])
        igdb_game_id_to_game_time_to_beat = {
            gttb.game_id: gttb for gttb in game_time_to_beats
        }

        for g in games:
            time_to_beat = igdb_game_id_to_game_time_to_beat.get(g.id, None)
            if time_to_beat:
                g.time_to_beat = time_to_beat

            for group in grouped_external_games:
                (group_game_id, ex_games) = group
                for ex in ex_games:
                    game_id_to_game[group_game_id].external_games.append(ex)

        return games

    def get_external_games(self, igdb_game_ids: list[int]):
        formatted_game_ids = self._format_ids(igdb_game_ids)
        endpoint = "external_games"
        query = f"""
            fields id, game, uid, external_game_source;
            where game = ({formatted_game_ids}) & external_game_source = 1;
            offset 0;
            limit {len(igdb_game_ids)};
        """

        response_bytes = self.igdb_wrapper.api_request(endpoint, query)
        response_json = json.loads(response_bytes)
        external_games = [
            ExternalGameResponse.model_validate(eg) for eg in response_json
        ]

        return external_games

    def get_game_time_to_beats(self, igdb_game_ids: list[int]):
        formatted_game_ids = self._format_ids(igdb_game_ids)
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
