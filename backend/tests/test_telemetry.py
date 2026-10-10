"""Unit tests for OpenTelemetry telemetry helpers."""

import os
from typing import cast

import pytest
from fastapi import FastAPI
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from sqlalchemy.engine import Engine

from app import telemetry
from app.settings import clear_settings_cache
from app.telemetry import (
    CredentialRedactingSpanProcessor,
    record_user_identity,
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
    """Restore telemetry module state and OTEL env vars after each test."""
    saved_env = {key: os.environ.get(key) for key in _OTEL_ENV_KEYS}
    saved_enabled = telemetry._enabled
    yield
    telemetry._enabled = saved_enabled
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

    monkeypatch.setattr("azure.monitor.opentelemetry.configure_azure_monitor", _record)

    telemetry.configure_telemetry(FastAPI())

    assert calls == []
    assert telemetry.is_telemetry_enabled() is False


def test_configure_telemetry_enables_and_passes_processor(
    monkeypatch, connection_string
):
    """With a connection string, configure the distro and instrument the app."""
    captured: dict = {}
    configure_calls: list[dict] = []
    instrument_app_calls: list = []
    httpx_instrument_calls: list = []

    def _configure(**kwargs):
        configure_calls.append(kwargs)

    monkeypatch.setattr(
        "azure.monitor.opentelemetry.configure_azure_monitor", _configure
    )
    monkeypatch.setattr(
        "opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app",
        lambda *args: instrument_app_calls.append(args[-1]),
    )
    monkeypatch.setattr(
        "opentelemetry.instrumentation.httpx.HTTPXClientInstrumentor.instrument",
        lambda *args, **kwargs: httpx_instrument_calls.append((args, kwargs)),
    )
    app = FastAPI()

    telemetry.configure_telemetry(app)

    assert telemetry.is_telemetry_enabled() is True
    assert "InstrumentationKey" in configure_calls[0]["connection_string"]
    assert isinstance(
        configure_calls[0]["span_processors"][0], CredentialRedactingSpanProcessor
    )
    assert instrument_app_calls == [app]
    assert len(httpx_instrument_calls) == 1
    assert os.environ["OTEL_TRACES_SAMPLER"] == "parentbased_trace_id_ratio"
    assert os.environ["OTEL_TRACES_SAMPLER_ARG"] == "1.0"
    assert os.environ["OTEL_SERVICE_NAME"] == "backlog-boss"
    assert captured == {}


def test_configure_telemetry_sampler_env_not_overridden(monkeypatch, connection_string):
    """Operator-supplied OTEL env vars must not be overwritten (setdefault)."""
    monkeypatch.setenv("OTEL_TRACES_SAMPLER", "always_on")
    monkeypatch.setattr(
        "azure.monitor.opentelemetry.configure_azure_monitor", lambda **kwargs: None
    )
    monkeypatch.setattr(
        "opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app",
        lambda *args: None,
    )
    monkeypatch.setattr(
        "opentelemetry.instrumentation.httpx.HTTPXClientInstrumentor.instrument",
        lambda *args, **kwargs: None,
    )

    telemetry.configure_telemetry(FastAPI())

    assert os.environ["OTEL_TRACES_SAMPLER"] == "always_on"


def test_configure_telemetry_fail_soft(monkeypatch, connection_string):
    """Exporter init failure must not raise and must leave telemetry disabled."""

    def _boom(**kwargs):
        raise RuntimeError("bad")

    monkeypatch.setattr("azure.monitor.opentelemetry.configure_azure_monitor", _boom)

    telemetry.configure_telemetry(FastAPI())

    assert telemetry.is_telemetry_enabled() is False


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


def test_record_user_identity_sets_attributes():
    """User identity lands on the active recording span."""
    provider = TracerProvider()
    tracer = provider.get_tracer("test")

    with tracer.start_as_current_span("req") as span:
        record_user_identity(42, "76561198000000000")

    attributes = cast(ReadableSpan, span).attributes
    assert attributes is not None
    assert attributes["user.id"] == 42
    assert attributes["user.steam_id"] == "76561198000000000"
    provider.shutdown()


def test_record_user_identity_noop_without_span():
    """Calling with no active span must not raise."""
    record_user_identity(1, "76561198000000000")


def test_instrument_engine_skipped_when_disabled(monkeypatch):
    """SQLAlchemy instrumentation is skipped when telemetry is off, run when on."""
    calls: list[dict] = []

    class _Recorder:
        def instrument(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(
        "opentelemetry.instrumentation.sqlalchemy.SQLAlchemyInstrumentor",
        _Recorder,
    )
    engine = cast(Engine, object())

    telemetry.instrument_engine(engine)
    assert calls == []

    telemetry._enabled = True
    telemetry.instrument_engine(engine)
    assert len(calls) == 1
    assert calls[0]["engine"] is engine


def test_shutdown_telemetry_is_safe_when_disabled():
    """Shutdown with telemetry never configured must be a no-op."""
    telemetry._enabled = False
    telemetry.shutdown_telemetry()
