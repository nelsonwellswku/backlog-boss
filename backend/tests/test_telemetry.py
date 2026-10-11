"""Unit tests for OpenTelemetry telemetry helpers."""

import asyncio
import logging
import os
from typing import cast

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from sqlalchemy.engine import Engine

from app import telemetry
from app.settings import clear_settings_cache, get_settings
from app.telemetry import (
    CredentialRedactingSpanProcessor,
    RequestSpanMiddleware,
    record_user_id,
    redact_credentials,
)

_OTEL_ENV_KEYS = (
    "APPLICATIONINSIGHTS_CONNECTION_STRING",
    "OTEL_SERVICE_NAME",
    "OTEL_TRACES_SAMPLER",
    "OTEL_TRACES_SAMPLER_ARG",
)


@pytest.fixture(autouse=True)
def _restore_telemetry_state():
    """Restore telemetry module state, logger levels and OTEL env vars."""
    saved_env = {key: os.environ.get(key) for key in _OTEL_ENV_KEYS}
    saved_enabled = telemetry._enabled
    saved_levels = {
        name: logging.getLogger(name).level
        for name in telemetry._NOISY_TELEMETRY_LOGGERS
    }
    # Start each test with telemetry disabled (empty value) so a local .env
    # cannot turn the "telemetry off" cases into "telemetry on" cases.
    os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = ""
    clear_settings_cache()
    yield
    telemetry._enabled = saved_enabled
    for name, level in saved_levels.items():
        logging.getLogger(name).setLevel(level)
    for key, value in saved_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    clear_settings_cache()


@pytest.fixture
def connection_string(monkeypatch):
    """Provide a syntactically valid connection string via settings env."""
    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=00000000-0000-0000-0000-000000000000;"
        "IngestionEndpoint=https://example.invalid/",
    )
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_configure_telemetry_is_noop_without_connection_string(monkeypatch):
    """Without a connection string the Azure distro must never be touched."""
    calls: list[dict] = []

    def _record(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("app.telemetry.configure_azure_monitor", _record)

    telemetry.configure_telemetry()

    assert calls == []
    assert telemetry.is_telemetry_enabled() is False


def test_configure_telemetry_enables_and_passes_processor(
    monkeypatch, connection_string
):
    """With a connection string, configure the distro with redacting processor."""
    for key in _OTEL_ENV_KEYS[1:]:
        monkeypatch.delenv(key, raising=False)
    configure_calls: list[dict] = []

    def _configure(**kwargs):
        configure_calls.append(kwargs)

    monkeypatch.setattr("app.telemetry.configure_azure_monitor", _configure)
    # Pin the OTEL settings so a local .env cannot change what is mirrored
    # into the process environment.
    settings = get_settings()
    settings.otel_service_name = "backlog-boss"
    settings.otel_traces_sampler = "parentbased_trace_id_ratio"
    settings.otel_traces_sampler_arg = "1.0"

    telemetry.configure_telemetry()

    assert telemetry.is_telemetry_enabled() is True
    assert "InstrumentationKey" in configure_calls[0]["connection_string"]
    assert isinstance(
        configure_calls[0]["span_processors"][0], CredentialRedactingSpanProcessor
    )
    assert configure_calls[0]["instrumentation_options"] == {
        "fastapi": {"enabled": False}
    }
    assert os.environ["OTEL_TRACES_SAMPLER"] == "parentbased_trace_id_ratio"
    assert os.environ["OTEL_TRACES_SAMPLER_ARG"] == "1.0"
    assert os.environ["OTEL_SERVICE_NAME"] == "backlog-boss"


def test_configure_telemetry_sampler_env_not_overridden(monkeypatch, connection_string):
    """Operator-supplied OTEL env vars must not be overwritten (setdefault)."""
    monkeypatch.setenv("OTEL_TRACES_SAMPLER", "always_on")
    monkeypatch.setattr("app.telemetry.configure_azure_monitor", lambda **kwargs: None)

    telemetry.configure_telemetry()

    assert os.environ["OTEL_TRACES_SAMPLER"] == "always_on"


def test_configure_telemetry_otel_defaults_come_from_settings(
    monkeypatch, connection_string
):
    """OTEL env defaults are mirrored from Settings rather than literals."""
    for key in ("OTEL_SERVICE_NAME", "OTEL_TRACES_SAMPLER", "OTEL_TRACES_SAMPLER_ARG"):
        monkeypatch.delenv(key, raising=False)
    settings = get_settings()
    settings.otel_service_name = "custom-service"
    settings.otel_traces_sampler = "always_on"
    settings.otel_traces_sampler_arg = "0.5"
    monkeypatch.setattr("app.telemetry.configure_azure_monitor", lambda **kwargs: None)

    telemetry.configure_telemetry()

    assert os.environ["OTEL_SERVICE_NAME"] == "custom-service"
    assert os.environ["OTEL_TRACES_SAMPLER"] == "always_on"
    assert os.environ["OTEL_TRACES_SAMPLER_ARG"] == "0.5"


def test_configure_telemetry_fail_soft(monkeypatch, connection_string):
    """Exporter init failure must not raise and must leave telemetry disabled."""

    def _boom(**kwargs):
        raise RuntimeError("bad")

    monkeypatch.setattr("app.telemetry.configure_azure_monitor", _boom)

    telemetry.configure_telemetry()

    assert telemetry.is_telemetry_enabled() is False


def test_configure_telemetry_second_call_is_noop(monkeypatch, connection_string):
    """Repeat configuration must not re-run the distro or duplicate exporters."""
    configure_calls: list[dict] = []

    def _configure(**kwargs):
        configure_calls.append(kwargs)

    monkeypatch.setattr("app.telemetry.configure_azure_monitor", _configure)

    telemetry.configure_telemetry()
    telemetry.configure_telemetry()

    assert len(configure_calls) == 1
    assert telemetry.is_telemetry_enabled() is True


def test_configure_telemetry_failure_after_success_keeps_enabled(
    monkeypatch, connection_string
):
    """A failed re-configuration must not disable a live pipeline."""
    monkeypatch.setattr("app.telemetry.configure_azure_monitor", lambda **kwargs: None)
    telemetry.configure_telemetry()
    assert telemetry.is_telemetry_enabled() is True

    def _boom(**kwargs):
        raise RuntimeError("bad")

    monkeypatch.setattr("app.telemetry.configure_azure_monitor", _boom)
    telemetry.configure_telemetry()

    assert telemetry.is_telemetry_enabled() is True


def test_configure_telemetry_silences_noisy_library_loggers(
    monkeypatch, connection_string
):
    """Azure/OTel library loggers must be raised to WARNING before export."""
    monkeypatch.setattr("app.telemetry.configure_azure_monitor", lambda **kwargs: None)
    logging.getLogger("azure").setLevel(logging.INFO)
    logging.getLogger("opentelemetry").setLevel(logging.INFO)

    telemetry.configure_telemetry()

    assert logging.getLogger("azure").level == logging.WARNING
    assert logging.getLogger("opentelemetry").level == logging.WARNING


def test_configure_telemetry_keeps_logger_levels_without_connection_string():
    """Telemetry off must leave library logger levels untouched."""
    logging.getLogger("azure").setLevel(logging.INFO)

    telemetry.configure_telemetry()

    assert logging.getLogger("azure").level == logging.INFO


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "https://api.steampowered.com/v1/?key=SECRET&format=json",
            "https://api.steampowered.com/v1/?key=REDACTED&format=json",
        ),
        ("https://example.com/?apikey=SECRET", "https://example.com/?apikey=REDACTED"),
        (
            "https://example.com/?access_token=SECRET",
            "https://example.com/?access_token=REDACTED",
        ),
        ("https://example.com/?token=SECRET", "https://example.com/?token=REDACTED"),
        (
            "https://id.twitch.tv/oauth2/token?client_id=abc&client_secret=SECRET&grant_type=client_credentials",
            "https://id.twitch.tv/oauth2/token?client_id=REDACTED&client_secret=REDACTED&grant_type=client_credentials",
        ),
        (
            "https://example.com/?client_secret=SECRET",
            "https://example.com/?client_secret=REDACTED",
        ),
        (
            "https://example.com/?Client_Secret=SECRET",
            "https://example.com/?Client_Secret=REDACTED",
        ),
        (
            "https://example.com/?client_id=abc",
            "https://example.com/?client_id=REDACTED",
        ),
        ("https://example.com/?secret=SECRET", "https://example.com/?secret=REDACTED"),
        (
            "https://example.com/?password=SECRET",
            "https://example.com/?password=REDACTED",
        ),
        ("https://example.com/?Key=SECRET", "https://example.com/?Key=REDACTED"),
        (
            "https://example.com/?key=SECRET&token=SECRET&x=1",
            "https://example.com/?key=REDACTED&token=REDACTED&x=1",
        ),
        ("https://example.com/path", "https://example.com/path"),
        ("https://user:pass@example.com/path", "https://REDACTED@example.com/path"),
        (
            "https://example.com/api/v1/resource",
            "https://example.com/api/v1/resource",
        ),
    ],
)
def test_redact_credentials(raw, expected):
    """Credential query params and userinfo are redacted; the rest is kept."""
    assert redact_credentials(raw) == expected


def test_redact_credentials_preserves_host_and_path():
    """Host and path must survive redaction of a credential-bearing URL."""
    result = redact_credentials("https://api.steampowered.com/v1/?key=SECRET")
    assert result.startswith("https://api.steampowered.com/v1/?")
    assert "SECRET" not in result


def test_span_processor_redacts_url_on_start():
    """on_start rewrites http.url but leaves other attributes alone."""
    provider = TracerProvider()
    tracer = provider.get_tracer("test")
    span = tracer.start_span(
        "x",
        attributes={
            "http.url": "https://api.steampowered.com/v1/?key=SECRET",
            "http.method": "GET",
        },
    )

    CredentialRedactingSpanProcessor().on_start(span, None)

    attributes = cast(ReadableSpan, span).attributes
    assert attributes is not None
    assert attributes["http.url"] == ("https://api.steampowered.com/v1/?key=REDACTED")
    assert attributes["http.method"] == "GET"
    span.end()
    provider.shutdown()


def test_span_processor_redacts_twitch_client_secret():
    """on_start rewrites url.full carrying Twitch OAuth secrets."""
    provider = TracerProvider()
    tracer = provider.get_tracer("test")
    span = tracer.start_span(
        "x",
        attributes={
            "url.full": "https://id.twitch.tv/oauth2/token?client_id=abc&client_secret=SECRET&grant_type=client_credentials",
        },
    )

    CredentialRedactingSpanProcessor().on_start(span, None)

    attributes = cast(ReadableSpan, span).attributes
    assert attributes is not None
    assert attributes["url.full"] == (
        "https://id.twitch.tv/oauth2/token?client_id=REDACTED&client_secret=REDACTED&grant_type=client_credentials"
    )
    span.end()
    provider.shutdown()


async def _noop_receive():
    """Stand-in ASGI receive callable for middleware tests."""
    return {"type": "http.request"}


async def _noop_send(message):
    """Stand-in ASGI send callable for middleware tests."""
    return None


def test_request_span_middleware_captures_server_span_on_scope():
    """The middleware stores the span current at entry onto the ASGI scope."""
    provider = TracerProvider()
    tracer = provider.get_tracer("test")
    seen: dict = {}

    async def inner(scope, receive, send):
        seen["scope"] = scope

    scope: dict = {"type": "http"}

    async def run():
        await RequestSpanMiddleware(inner)(scope, _noop_receive, _noop_send)

    with tracer.start_as_current_span("GET /x") as span:
        asyncio.run(run())

    assert scope[telemetry._SERVER_SPAN_SCOPE_KEY] is span
    provider.shutdown()


def test_request_span_middleware_ignores_lifespan_scope():
    """Non-HTTP scopes (lifespan) must not be stamped with a span key."""

    async def inner(scope, receive, send):
        pass

    scope: dict = {"type": "lifespan"}

    async def run():
        await RequestSpanMiddleware(inner)(scope, _noop_receive, _noop_send)

    asyncio.run(run())

    assert telemetry._SERVER_SPAN_SCOPE_KEY not in scope


def test_record_user_id_uses_span_captured_on_scope():
    """Identity must land on the captured server span, not the current child."""
    provider = TracerProvider()
    tracer = provider.get_tracer("test")
    server_span = tracer.start_span("GET /api/me")
    request = Request(
        scope={"type": "http", telemetry._SERVER_SPAN_SCOPE_KEY: server_span}
    )

    with tracer.start_as_current_span("fastapi.dependencies"):
        record_user_id(request, 42)

    server_attributes = cast(ReadableSpan, server_span).attributes
    assert server_attributes is not None
    assert server_attributes["user.user_id"] == 42
    assert "user.steam_id" not in server_attributes
    server_span.end()
    provider.shutdown()


def test_record_user_id_falls_back_to_current_span():
    """Without a captured span, stamp the active recording span as a fallback."""
    provider = TracerProvider()
    tracer = provider.get_tracer("test")
    request = Request(scope={"type": "http"})

    with tracer.start_as_current_span("req") as span:
        record_user_id(request, 42)

    attributes = cast(ReadableSpan, span).attributes
    assert attributes is not None
    assert attributes["user.user_id"] == 42
    provider.shutdown()


def test_record_user_id_on_real_request_span():
    """End to end: user id lands on the SERVER span App Insights exports as a Request."""
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    app = FastAPI(telemetry={"tracer_provider": provider})
    app.add_middleware(RequestSpanMiddleware)

    @app.get("/me")
    def me(request: Request):
        record_user_id(request, 42)
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/me")
    assert response.status_code == 200

    spans = {span.name: span for span in exporter.get_finished_spans()}
    server_attributes = spans["GET /me"].attributes
    assert server_attributes is not None
    assert server_attributes["user.user_id"] == 42
    for name, span in spans.items():
        if name != "GET /me":
            assert "user.user_id" not in (span.attributes or {}), name
    provider.shutdown()


def test_record_user_id_noop_without_span():
    """Calling with no active span must not raise."""
    record_user_id(Request(scope={"type": "http"}), 1)


def test_instrument_engine_always_instruments(monkeypatch):
    """Engine instrumentation must not depend on telemetry-enabled ordering."""
    calls: list[dict] = []

    class _Recorder:
        def instrument(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr("app.telemetry.SQLAlchemyInstrumentor", _Recorder)
    engine = cast(Engine, object())

    telemetry._enabled = False
    telemetry.instrument_engine(engine)
    assert len(calls) == 1
    assert calls[0]["engine"] is engine

    telemetry._enabled = True
    telemetry.instrument_engine(engine)
    assert len(calls) == 2
    assert calls[1]["engine"] is engine


def test_shutdown_telemetry_is_safe_when_disabled():
    """Shutdown with telemetry never configured must be a no-op."""
    telemetry._enabled = False
    telemetry.shutdown_telemetry()


def test_shutdown_telemetry_shuts_down_all_providers(monkeypatch):
    """Trace, metrics, and logs providers must all be shut down."""
    shutdown_calls: list[str] = []

    class _Provider:
        def __init__(self, name: str) -> None:
            self._name = name

        def shutdown(self) -> None:
            """Record shutdown for provider ordering assertions."""
            shutdown_calls.append(self._name)

    monkeypatch.setattr(
        "app.telemetry.trace.get_tracer_provider",
        lambda: _Provider("trace"),
    )
    monkeypatch.setattr(
        "app.telemetry.metrics.get_meter_provider",
        lambda: _Provider("metrics"),
    )
    monkeypatch.setattr(
        "app.telemetry.get_logger_provider",
        lambda: _Provider("logs"),
    )
    telemetry._enabled = True

    telemetry.shutdown_telemetry()

    assert sorted(shutdown_calls) == ["logs", "metrics", "trace"]
    assert telemetry.is_telemetry_enabled() is False


def test_shutdown_telemetry_continues_on_provider_failure(monkeypatch):
    """One failing provider must not prevent the others from shutting down."""
    shutdown_calls: list[str] = []

    class _FailingProvider:
        def shutdown(self) -> None:
            """Simulate an exporter flush failure during shutdown."""
            raise RuntimeError("flush failed")

    class _RecordingProvider:
        def shutdown(self) -> None:
            """Record successful shutdown after a sibling failure."""
            shutdown_calls.append("ok")

    monkeypatch.setattr(
        "app.telemetry.trace.get_tracer_provider",
        _FailingProvider,
    )
    monkeypatch.setattr(
        "app.telemetry.metrics.get_meter_provider",
        _RecordingProvider,
    )
    monkeypatch.setattr(
        "app.telemetry.get_logger_provider",
        _RecordingProvider,
    )
    telemetry._enabled = True

    telemetry.shutdown_telemetry()

    assert shutdown_calls == ["ok", "ok"]
    assert telemetry.is_telemetry_enabled() is False
