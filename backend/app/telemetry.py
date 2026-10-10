"""OpenTelemetry telemetry export to Azure Application Insights."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import Span, Tracer

from app.settings import get_settings

# TODO: Why does this need to be here?
if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_CREDENTIAL_QUERY_PARAMS = frozenset(
    {"key", "apikey", "api_key", "access_token", "token"}
)
_REDACTED = "REDACTED"
_URL_ATTRIBUTE_KEYS = ("http.url", "url.full", "http.target", "url.query")

_enabled = False


def redact_credentials(url: str) -> str:
    """Replace credential-bearing values in a URL.

    Redacts query parameter values for credential-style parameter names and
    any userinfo portion of the authority. Path, host, fragment, and all
    other query parameters are preserved.

    Args:
        url: URL captured on a span attribute.

    Returns:
        The URL with credential values replaced by "REDACTED".
    """
    parts = urlsplit(url)
    netloc = parts.netloc
    if "@" in netloc:
        netloc = f"{_REDACTED}@{netloc.rsplit('@', 1)[1]}"

    query_pairs = parse_qsl(parts.query, keep_blank_values=True)
    if not any(name.lower() in _CREDENTIAL_QUERY_PARAMS for name, _ in query_pairs):
        if netloc == parts.netloc:
            return url
        return urlunsplit(
            (parts.scheme, netloc, parts.path, parts.query, parts.fragment)
        )

    redacted_query = urlencode(
        [
            (name, _REDACTED if name.lower() in _CREDENTIAL_QUERY_PARAMS else value)
            for name, value in query_pairs
        ]
    )
    return urlunsplit(
        (parts.scheme, netloc, parts.path, redacted_query, parts.fragment)
    )


class CredentialRedactingSpanProcessor(SpanProcessor):
    """Rewrites credential-bearing URL attributes on spans before export."""

    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        """Redact URL attributes on a newly started recording span.

        Called at span start because SDK span attributes become immutable the
        moment the span ends, and httpx/requests instrumentations set their
        URL attributes when the span is created.

        Args:
            span: The recording span being started.
            parent_context: Ignored; required by the SpanProcessor interface.
        """
        attributes = getattr(span, "attributes", None)
        if not attributes:
            return
        for key in _URL_ATTRIBUTE_KEYS:
            value = attributes.get(key)
            if isinstance(value, str):
                redacted = redact_credentials(value)
                if redacted != value:
                    span.set_attribute(key, redacted)


def configure_telemetry(app: FastAPI) -> None:
    """Configure OpenTelemetry export to Azure Application Insights.

    No-op when APPLICATIONINSIGHTS_CONNECTION_STRING is unset, so the app
    behaves exactly as before. Never raises: any setup failure (invalid
    connection string, missing package, exporter init error) is logged once
    and leaves telemetry disabled.

    Args:
        app: The FastAPI application to instrument.
    """
    global _enabled
    settings = get_settings()
    if not settings.applicationinsights_connection_string:
        return

    try:
        # TODO: These env variables should be set to the values from the settings object
        os.environ.setdefault("OTEL_SERVICE_NAME", "backlog-boss")
        os.environ.setdefault("OTEL_TRACES_SAMPLER", "parentbased_trace_id_ratio")
        os.environ.setdefault("OTEL_TRACES_SAMPLER_ARG", "1.0")

        # TODO: do we need these lazy loaded imports? app crash is _preferable_ because these should always be available.
        # Imported lazily so a broken/missing Azure package cannot crash app import.
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string,
            span_processors=[CredentialRedactingSpanProcessor()],
        )

        # The app was instantiated at import time, before the distro swapped
        # fastapi.FastAPI, so it is not covered by auto-instrumentation.
        FastAPIInstrumentor().instrument_app(app)

        httpx_instrumentor = HTTPXClientInstrumentor()
        if not getattr(httpx_instrumentor, "_is_instrumented_by_opentelemetry", False):
            httpx_instrumentor.instrument()

        _enabled = True
    except Exception:
        logger.exception("Telemetry configuration failed; continuing without telemetry")
        _enabled = False


def shutdown_telemetry() -> None:
    """Flush pending telemetry and shut down the OpenTelemetry providers.

    Safe to call when telemetry was never configured. Each provider is shut
    down independently and failures are swallowed so shutdown never blocks or
    crashes the process. The TracerProvider also registers an atexit flush as
    a backstop; provider shutdown is idempotent.
    """
    global _enabled
    if not _enabled:
        return

    from opentelemetry._logs import get_logger_provider

    for get_provider in (trace.get_tracer_provider, get_logger_provider):
        try:
            provider = get_provider()
            shutdown = getattr(provider, "shutdown", None)
            if callable(shutdown):
                shutdown()
        except Exception:
            logger.exception("Failed to shut down telemetry provider")

    _enabled = False


def is_telemetry_enabled() -> bool:
    """Return whether telemetry was successfully configured this process."""
    return _enabled


def get_tracer(name: str) -> Tracer:
    """Return a tracer for the given instrumentation scope.

    Args:
        name: Instrumentation scope name, usually ``__name__``.

    Returns:
        A tracer that yields no-op spans when telemetry is not configured.
    """
    return trace.get_tracer(name)


def instrument_engine(engine: Engine) -> None:
    """Attach SQLAlchemy instrumentation to an engine when telemetry is enabled.

    The distro does not cover pyodbc, so this is the only SQLAlchemy
    instrumentation. Called once per process because ``get_db_engine`` is
    lru_cached; tests run with telemetry disabled so this is inert there.

    Args:
        engine: The SQLAlchemy engine created by ``get_db_engine``.
    """
    if not _enabled:
        return
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(engine=engine)


def record_user_identity(app_user_id: int, steam_id: str) -> None:
    """Attach user identity attributes to the active span, if recording.

    No-op when no span is active or telemetry is disabled, so callers need
    no guards.

    Args:
        app_user_id: Internal application user id.
        steam_id: Steam id of the user.
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attribute("user.id", app_user_id)
        span.set_attribute("user.steam_id", steam_id)
