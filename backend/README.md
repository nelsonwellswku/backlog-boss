# Backlog Boss

FastAPI powered backend for Backlog Boss

## Environment variables

For local development, copy the [sample env](./.env.sample) as `.env` and fill in the values.

A handful of environment variables are required. Some are secrets from 3rd party sources.

[Steam API Key](https://steamcommunity.com/dev/apikey)

[Twitch / IGDB Credentials](https://api-docs.igdb.com/#getting-started)

## Formatting

The backend uses `ruff` to ensure Python code format rules.

```
ruff format
```

## Testing

Database-backed tests use Testcontainers to start disposable SQL Server and Grate containers, create a fresh database, apply the SQL migrations from `../migrations` through Grate, and remove the containers when `pytest` exits.

Run the backend test suite with:

```
uv run pytest -q
```

Docker must be available locally for the database scaffold to start.
