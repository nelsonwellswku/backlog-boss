from logging import getLogger

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.engine import create_db_session
from app.database.models import BacklogGame, IgdbGame, IgdbGameGenre, IgdbGenre
from app.infrastructure.igdb_client import IgdbClient

logger = getLogger(__name__)


def fetch_missing_genres_task(backlog_id: int, db: Session | None = None) -> None:
    try:
        if db is not None:
            _run(backlog_id, db)
        else:
            with create_db_session() as session:
                _run(backlog_id, session)
    except Exception:
        logger.exception("Failed to fetch missing genres for backlog %d", backlog_id)


def _run(backlog_id: int, db: Session) -> None:
    stmt = (
        select(IgdbGame.igdb_game_id)
        .join(BacklogGame)
        .where(BacklogGame.backlog_id == backlog_id)
        .where(
            ~select(IgdbGameGenre.igdb_game_id)
            .where(IgdbGameGenre.igdb_game_id == IgdbGame.igdb_game_id)
            .exists()
        )
    )
    game_ids = list(db.scalars(stmt).all())

    if not game_ids:
        logger.info("No games missing genres in backlog %d", backlog_id)
        return

    igdb_client = IgdbClient.create()
    genres_by_game = igdb_client.get_genres_by_game_ids(game_ids)

    if not genres_by_game:
        logger.info(
            "IGDB returned no genres for %d games in backlog %d",
            len(game_ids),
            backlog_id,
        )
        return

    updated = 0
    for igdb_game_id, genre_list in genres_by_game.items():
        stmt = (
            select(IgdbGame)
            .where(IgdbGame.igdb_game_id == igdb_game_id)
            .where(
                ~select(IgdbGameGenre.igdb_game_id)
                .where(IgdbGameGenre.igdb_game_id == IgdbGame.igdb_game_id)
                .exists()
            )
            .options(selectinload(IgdbGame.genres))
        )
        game = db.scalars(stmt).one_or_none()
        if not game:
            continue

        for genre_response in genre_list:
            genre = db.get(IgdbGenre, genre_response.id)
            if not genre:
                genre = IgdbGenre(
                    igdb_genre_id=genre_response.id,
                    name=genre_response.name,
                )
                db.add(genre)
            game.genres.append(genre)
            updated += 1

    db.commit()
    logger.info(
        "Updated genres for %d games in backlog %d",
        updated,
        backlog_id,
    )
