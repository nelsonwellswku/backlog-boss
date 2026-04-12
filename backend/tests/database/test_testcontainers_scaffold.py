from sqlalchemy import text
from sqlalchemy.engine import Engine


def test_database_migrations_are_applied(database_engine: Engine):
    with database_engine.connect() as connection:
        actual = connection.execute(
            text("SELECT [Name] FROM bb.IgdbExternalGameSource WHERE Id = 1")
        ).scalar_one()

    assert actual == "Steam"
