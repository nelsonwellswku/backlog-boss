from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    IgdbExternalGame,
    IgdbGame,
    IgdbGameTimeToBeat,
    IgdbGenre,
)
from app.infrastructure.igdb_client import IgdbGameResponse


def persist_igdb_games(db: Session, games: list[IgdbGameResponse]) -> bool:
    if not games:
        return False

    game_ids = [game.id for game in games]
    existing_game_ids = set(
        db.scalars(
            select(IgdbGame.igdb_game_id).where(IgdbGame.igdb_game_id.in_(game_ids))
        ).all()
    )

    candidate_external_uids: set[int] = set()
    for game in games:
        if game.id in existing_game_ids:
            continue

        for external_game in game.external_games:
            parsed_uid = _parse_external_uid(external_game.uid)
            if parsed_uid is not None:
                candidate_external_uids.add(parsed_uid)

    existing_external_uids = set(
        db.scalars(
            select(IgdbExternalGame.uid).where(
                IgdbExternalGame.igdb_external_game_source_id == 1,
                IgdbExternalGame.uid.in_(candidate_external_uids),
            )
        ).all()
    )

    all_genre_ids: set[int] = set()
    for game in games:
        for g in game.genres:
            all_genre_ids.add(g.id)

    existing_genre_ids = set(
        db.scalars(
            select(IgdbGenre.igdb_genre_id).where(
                IgdbGenre.igdb_genre_id.in_(all_genre_ids)
            )
        ).all()
    )

    genre_cache: dict[int, IgdbGenre] = {}
    for genre_id in all_genre_ids:
        if genre_id in existing_genre_ids:
            genre_obj = db.get(IgdbGenre, genre_id)
            assert genre_obj is not None
            genre_cache[genre_id] = genre_obj

    games_to_add: list[IgdbGame] = []
    for game in games:
        if game.id in existing_game_ids:
            continue

        igdb_game = IgdbGame(
            igdb_game_id=game.id,
            name=game.name,
            total_rating=game.total_rating,
            cover_image_id=game.cover.image_id if game.cover else None,
        )

        if game.time_to_beat:
            igdb_game.time_to_beat = IgdbGameTimeToBeat(
                igdb_game_time_to_beat_id=game.time_to_beat.id,
                igdb_game_id=game.id,
                normally=game.time_to_beat.normally,
            )

        for genre in game.genres:
            if genre.id not in genre_cache:
                genre_obj = IgdbGenre(igdb_genre_id=genre.id, name=genre.name)
                db.add(genre_obj)
                genre_cache[genre.id] = genre_obj
            igdb_game.genres.append(genre_cache[genre.id])

        for external_game in game.external_games:
            parsed_uid = _parse_external_uid(external_game.uid)
            if parsed_uid is None or parsed_uid in existing_external_uids:
                continue

            igdb_game.external_games.append(
                IgdbExternalGame(
                    igdb_external_game_id=external_game.id,
                    uid=parsed_uid,
                    igdb_external_game_source_id=1,
                )
            )
            existing_external_uids.add(parsed_uid)

        games_to_add.append(igdb_game)

    if not games_to_add:
        return False

    db.add_all(games_to_add)
    db.flush()
    return True


def _parse_external_uid(uid: str) -> int | None:
    try:
        return int(uid)
    except ValueError:
        # Steam games should have integer UIDs, but IGDB can occasionally
        # contain malformed comma-delimited values.
        return None
