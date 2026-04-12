from app.features.auth.get_current_user import User
from app.features.user.get_me_handler import GetMeHandler, GetMeResponse


def test_handle_returns_current_user_details():
    current_user = User(
        app_user_id=123,
        steam_id="76561198000000000",
        persona_name="Test Persona",
        first_name="Test",
        last_name="User",
    )
    handler = GetMeHandler(current_user)

    actual = handler.handle()

    assert actual == GetMeResponse(
        app_user_id=123,
        steam_id="76561198000000000",
        persona_name="Test Persona",
    )
