from app.oauth_device_flow import (
    AuthorizationDenied,
    AuthorizationExpired,
    DeviceAuthorization,
    DeviceFlowClient,
    TokenRefreshError,
)
from app.token_store import TokenSet


class FakeResponse:
    def __init__(self, payload: dict, ok: bool = True) -> None:
        self.payload = payload
        self.ok = ok

    def json(self) -> dict:
        return self.payload

    def raise_for_status(self) -> None:
        if not self.ok:
            raise RuntimeError(self.payload)


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses

    def post(self, *args, **kwargs) -> FakeResponse:
        return self.responses.pop(0)


def authorization() -> DeviceAuthorization:
    return DeviceAuthorization(
        device_code="device",
        user_code="ABC123",
        verification_uri="https://example.test/device",
        verification_uri_complete="https://example.test/device?code=ABC123",
        expires_in=900,
        interval=1,
    )


def test_poll_once_pending() -> None:
    client = DeviceFlowClient("auth", "token", "client", "scope", FakeSession([
        FakeResponse({"error": "authorization_pending"}, ok=False)
    ]))

    assert client.poll_once(authorization()) == "authorization_pending"


def test_poll_once_slow_down() -> None:
    client = DeviceFlowClient("auth", "token", "client", "scope", FakeSession([
        FakeResponse({"error": "slow_down"}, ok=False)
    ]))

    assert client.poll_once(authorization()) == "slow_down"


def test_poll_once_success() -> None:
    client = DeviceFlowClient("auth", "token", "client", "scope", FakeSession([
        FakeResponse({"access_token": "a", "refresh_token": "r", "expires_in": 3600})
    ]))

    assert isinstance(client.poll_once(authorization()), TokenSet)


def test_poll_once_denied() -> None:
    client = DeviceFlowClient("auth", "token", "client", "scope", FakeSession([
        FakeResponse({"error": "access_denied"}, ok=False)
    ]))

    try:
        client.poll_once(authorization())
    except AuthorizationDenied:
        return
    raise AssertionError("expected AuthorizationDenied")


def test_poll_once_expired() -> None:
    client = DeviceFlowClient("auth", "token", "client", "scope", FakeSession([
        FakeResponse({"error": "expired_token"}, ok=False)
    ]))

    try:
        client.poll_once(authorization())
    except AuthorizationExpired:
        return
    raise AssertionError("expected AuthorizationExpired")


def test_refresh_uses_existing_refresh_token_when_not_rotated() -> None:
    client = DeviceFlowClient(
        "auth",
        "token",
        "client",
        "scope",
        FakeSession([FakeResponse({"access_token": "new-access", "expires_in": 3600})]),
    )

    refreshed = client.refresh(
        TokenSet(
            access_token="old-access",
            refresh_token="old-refresh",
            expires_at=1,
        )
    )

    assert refreshed.access_token == "new-access"
    assert refreshed.refresh_token == "old-refresh"


def test_refresh_uses_rotated_refresh_token() -> None:
    client = DeviceFlowClient(
        "auth",
        "token",
        "client",
        "scope",
        FakeSession(
            [
                FakeResponse(
                    {
                        "access_token": "new-access",
                        "refresh_token": "new-refresh",
                        "expires_in": 3600,
                    }
                )
            ]
        ),
    )

    refreshed = client.refresh(
        TokenSet(
            access_token="old-access",
            refresh_token="old-refresh",
            expires_at=1,
        )
    )

    assert refreshed.access_token == "new-access"
    assert refreshed.refresh_token == "new-refresh"


def test_refresh_rejects_invalid_grant() -> None:
    client = DeviceFlowClient(
        "auth",
        "token",
        "client",
        "scope",
        FakeSession([FakeResponse({"error": "invalid_grant"}, ok=False)]),
    )

    try:
        client.refresh(TokenSet(access_token="old-access", refresh_token="old-refresh", expires_at=1))
    except TokenRefreshError:
        return
    raise AssertionError("expected TokenRefreshError")
