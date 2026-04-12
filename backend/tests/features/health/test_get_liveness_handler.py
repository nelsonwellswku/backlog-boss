from app.features.health.get_liveness_handler import (
    GetLivenessHandler,
    GetLivenessResponse,
)


def test_handle_returns_service_up_message():
    handler = GetLivenessHandler()

    actual = handler.handle()

    assert actual == GetLivenessResponse(message="Service is up.")
