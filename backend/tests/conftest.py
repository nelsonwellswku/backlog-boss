import os
import time
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.mssql import SqlServerContainer

from app.database.engine import create_db_session, get_db_engine, reset_db_engine
from app.settings import Settings, clear_settings_cache

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_ROOT = REPO_ROOT / "migrations"
SQL_SERVER_IMAGE = "mcr.microsoft.com/mssql/server:2025-latest"
GRATE_IMAGE = "erikbra/grate:2.0.0"
SQL_SERVER_USER = "sa"
SQL_SERVER_PASSWORD = "Testcontainers1!"
GRATE_SCHEMA = "bbgrate"
ENV_KEYS = (
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
    "DB_DATABASE",
    "TWITCH_CLIENT_ID",
    "TWITCH_CLIENT_SECRET",
    "STEAM_API_KEY",
)


def _run_grate(*, network: Network, database: str) -> None:
    grate_command = [
        "--connstring="
        f"Server=sqlserver;Database={database};User Id={SQL_SERVER_USER};"
        f"Password={SQL_SERVER_PASSWORD};TrustServerCertificate=True",
        "--sqlfilesdirectory=/db",
        "--version=1.0.0.0",
        "--databasetype=sqlserver",
        "--transaction=true",
        "--silent=false",
        "--createdatabase=true",
        f"--schema={GRATE_SCHEMA}",
        "--environment=LOCAL",
    ]

    with (
        DockerContainer(GRATE_IMAGE)
        .with_kwargs(entrypoint="./grate")
        .with_command(grate_command)
        .with_network(network)
        .with_volume_mapping(MIGRATIONS_ROOT, "/db", "ro") as container
    ):
        result = container.get_wrapped_container().wait(timeout=120)
        if result["StatusCode"] == 0:
            return

        stdout, stderr = container.get_logs()
        raise RuntimeError(
            "Grate migration failed:\n"
            f"{stdout.decode('utf-8', errors='replace')}\n"
            f"{stderr.decode('utf-8', errors='replace')}"
        )


def _set_test_environment(
    *, host: str, port: int, database: str
) -> dict[str, str | None]:
    original_env = {key: os.environ.get(key) for key in ENV_KEYS}
    os.environ.update(
        {
            "DB_HOST": host,
            "DB_PORT": str(port),
            "DB_USER": SQL_SERVER_USER,
            "DB_PASSWORD": SQL_SERVER_PASSWORD,
            "DB_DATABASE": database,
            "TWITCH_CLIENT_ID": "test-client-id",
            "TWITCH_CLIENT_SECRET": "test-client-secret",
            "STEAM_API_KEY": "test-steam-api-key",
        }
    )
    clear_settings_cache()
    reset_db_engine()
    return original_env


def _restore_environment(original_env: dict[str, str | None]) -> None:
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    reset_db_engine()
    clear_settings_cache()


def _wait_for_application_database(timeout_seconds: float = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: OperationalError | None = None

    while time.monotonic() < deadline:
        try:
            with get_db_engine().connect():
                return
        except OperationalError as exc:
            last_error = exc
            time.sleep(1)

    if last_error is not None:
        raise last_error


@pytest.fixture(scope="session", autouse=True)
def database_container() -> Iterator[None]:
    database_name = f"BacklogBossTest_{uuid4().hex}"

    with (
        Network() as network,
        SqlServerContainer(
            image=SQL_SERVER_IMAGE,
            username=SQL_SERVER_USER,
            password=SQL_SERVER_PASSWORD,
            dbname="master",
        )
        .with_network(network)
        .with_network_aliases("sqlserver") as container,
    ):
        host = container.get_container_host_ip()
        port = container.get_exposed_port(1433)

        _run_grate(network=network, database=database_name)
        original_env = _set_test_environment(
            host=host, port=port, database=database_name
        )
        _wait_for_application_database()

        try:
            yield
        finally:
            _restore_environment(original_env)


@pytest.fixture(scope="session")
def database_engine(database_container: None) -> Iterator[Engine]:
    yield get_db_engine()


@pytest.fixture
def db_session(database_engine: Engine):
    with create_db_session(database_engine) as session:
        yield session


@pytest.fixture
def dummy_settings() -> Settings:
    return Settings(
        db_host="localhost",
        db_user="sa",
        db_password="password",
        db_database="BacklogBoss",
        twitch_client_id="twitch-client-id",
        twitch_client_secret="twitch-client-secret",
        steam_api_key="steam-api-key",
        base_url="https://backlogboss.example.com/",
    )
