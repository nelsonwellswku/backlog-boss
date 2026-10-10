"""Chained application lifespan for HTTP client and telemetry setup."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.http_client import configure_httpx_lifespan
from app.telemetry import configure_telemetry, shutdown_telemetry


# TODO: Fix this deprecation
@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run application startup and shutdown hooks.

    Configures telemetry before the shared HTTP client is created so client
    spans are captured, then flushes telemetry during shutdown.

    Args:
        app: The FastAPI application being served.

    Yields:
        Control to the server while the application is running.
    """
    configure_telemetry(app)
    try:
        async with configure_httpx_lifespan(app):
            yield
    finally:
        shutdown_telemetry()
