from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import IgdbExternalGame, IgdbGame, IgdbGameTimeToBeat
from app.infrastructure.igdb_client import IgdbGameResponse


def persist_igdb_games(db: Session, games: list[IgdbGameResponse]) -> None:
    if not games:
        return

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

    games_to_add: list[IgdbGame] = []
    for game in games:
        if game.id in existing_game_ids:
            continue

        igdb_game = IgdbGame(
            igdb_game_id=game.id,
            name=game.name,
            total_rating=game.total_rating,
        )

        if game.time_to_beat:
            igdb_game.time_to_beat = IgdbGameTimeToBeat(
                igdb_game_time_to_beat_id=game.time_to_beat.id,
                igdb_game_id=game.id,
                normally=game.time_to_beat.normally,
            )

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
        return

    db.add_all(games_to_add)
    db.flush()


def _parse_external_uid(uid: str) -> int | None:
    try:
        return int(uid)
    except ValueError:
        # Steam games should have integer UIDs, but IGDB can occasionally
        # contain malformed comma-delimited values.
        return None
