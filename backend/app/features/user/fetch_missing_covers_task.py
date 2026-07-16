from logging import getLogger

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.engine import create_db_session
from app.database.models import BacklogGame, IgdbGame
from app.infrastructure.igdb_client import IgdbClient

logger = getLogger(__name__)


def fetch_missing_covers_task(backlog_id: int, db: Session | None = None) -> None:
    try:
        if db is not None:
            _run(backlog_id, db)
        else:
            with create_db_session() as session:
                _run(backlog_id, session)
    except Exception:
        logger.exception("Failed to fetch missing covers for backlog %d", backlog_id)


def _run(backlog_id: int, db: Session) -> None:
    stmt = (
        select(IgdbGame.igdb_game_id)
        .join(BacklogGame)
        .where(BacklogGame.backlog_id == backlog_id)
        .where(IgdbGame.cover_image_id.is_(None))
    )
    game_ids = list(db.scalars(stmt).all())

    if not game_ids:
        logger.info("No games missing covers in backlog %d", backlog_id)
        return

    igdb_client = IgdbClient.create()
    covers = igdb_client.get_covers_by_game_ids(game_ids)

    if not covers:
        logger.info(
            "IGDB returned no covers for %d games in backlog %d",
            len(game_ids),
            backlog_id,
        )
        return

    updated = 0
    for igdb_game_id, image_id in covers.items():
        stmt = (
            select(IgdbGame)
            .where(IgdbGame.igdb_game_id == igdb_game_id)
            .where(IgdbGame.cover_image_id.is_(None))
        )
        game = db.scalars(stmt).one_or_none()
        if game:
            game.cover_image_id = image_id
            updated += 1

    db.commit()
    logger.info(
        "Updated covers for %d games in backlog %d",
        updated,
        backlog_id,
    )
