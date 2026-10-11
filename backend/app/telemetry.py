"""OpenTelemetry telemetry export to Azure Application Insights."""

from __future__ import annotations

import logging
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry._logs import get_logger_provider
from opentelemetry.context import Context
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import Span, Tracer
from sqlalchemy.engine import Engine
from starlette.types import ASGIApp, Receive, Scope, Send

from app.settings import get_settings

logger = logging.getLogger(__name__)

_CREDENTIAL_QUERY_PARAMS = frozenset(
    {"key", "apikey", "api_key", "access_token", "token"}
)
_REDACTED = "REDACTED"
_URL_ATTRIBUTE_KEYS = ("http.url", "url.full", "http.target", "url.query")

_enabled = False

# Library loggers that emit routine chatter at INFO on every export cycle:
# azure.core logs the full ingestion request/response, the Azure exporter logs
# "Transmission succeeded", and the OpenTelemetry SDK logs shutdown notes.
_NOISY_TELEMETRY_LOGGERS = ("azure", "opentelemetry")


def _silence_noisy_telemetry_loggers() -> None:
    """Raise the level of telemetry library loggers to WARNING.

    The Azure distro bridges the root logger into Application Insights, so
    INFO records from these libraries are both printed locally and fed back
    into the exporter — which itself logs an INFO line per successful POST,
    triggering the "recursive logging, skipping" guard. WARNING keeps
    genuine export and configuration failures visible while dropping the
    per-cycle noise.
    """
    for name in _NOISY_TELEMETRY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


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
    connection string, exporter init error) is logged once and leaves
    telemetry disabled.

    The Azure distro reads OTEL_SERVICE_NAME and the sampler configuration
    from the process environment, so those Settings values are mirrored into
    ``os.environ`` via ``setdefault`` and an operator-supplied OTEL_* variable
    always wins.

    Before configuring the distro, the ``azure`` and ``opentelemetry``
    library loggers are raised to WARNING so the exporter's per-cycle INFO
    chatter (ingestion HTTP logging, "Transmission succeeded" summaries)
    stays out of the console and out of the exported telemetry.

    Args:
        app: The FastAPI application to instrument.
    """
    global _enabled
    settings = get_settings()
    if not settings.applicationinsights_connection_string:
        return

    try:
        os.environ.setdefault("OTEL_SERVICE_NAME", settings.otel_service_name)
        os.environ.setdefault("OTEL_TRACES_SAMPLER", settings.otel_traces_sampler)
        os.environ.setdefault(
            "OTEL_TRACES_SAMPLER_ARG", settings.otel_traces_sampler_arg
        )

        _silence_noisy_telemetry_loggers()

        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string,
            span_processors=[CredentialRedactingSpanProcessor()],
        )

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

    SQLAlchemyInstrumentor().instrument(engine=engine)


_SERVER_SPAN_SCOPE_KEY = "backlog_boss.server_span"


class RequestSpanMiddleware:
    """ASGI middleware that stores the request's server span on the scope.

    FastAPI's native telemetry makes the HTTP SERVER span current while it
    runs the middleware stack, but dependency resolution later switches to
    INTERNAL child spans (``fastapi.dependencies`` / ``fastapi.endpoint``),
    which Application Insights exports as "InProc" dependencies rather than
    the Request item. Capturing the span here — while it is still current —
    lets ``record_user_id`` stamp request-scoped attributes onto the span
    that becomes the Request telemetry item.

    Uses only the public OpenTelemetry API and the plain ASGI ``scope``, so
    it does not depend on FastAPI internals.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Capture the current server span onto the scope for HTTP traffic.

        Args:
            scope: The ASGI connection scope.
            receive: ASGI receive callable.
            send: ASGI send callable.
        """
        if scope["type"] in ("http", "websocket"):
            scope[_SERVER_SPAN_SCOPE_KEY] = trace.get_current_span()
        await self.app(scope, receive, send)


def record_user_id(request: Request, user_id: int) -> None:
    """Set the ``user.user_id`` custom dimension on the request's server span.

    Prefers the span captured by ``RequestSpanMiddleware`` so the attribute
    lands on the Application Insights Request item; falls back to the current
    span when no capture is present (for example a request that bypassed the
    middleware). No-op when no span is recording or telemetry is disabled, so
    callers need no guards.

    Args:
        request: The current HTTP request, carrying the captured server span.
        user_id: Internal application user id.
    """
    span = request.scope.get(_SERVER_SPAN_SCOPE_KEY) or trace.get_current_span()
    if span.is_recording():
        span.set_attribute("user.user_id", user_id)
