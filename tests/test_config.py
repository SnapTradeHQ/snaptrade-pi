import os

from app.config import load_settings


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, str]:
        return {
            "device_authorization_endpoint": "https://example.test/device",
            "token_endpoint": "https://example.test/token",
            "revocation_endpoint": "https://example.test/revoke",
        }


def test_load_settings_discovers_oauth_metadata(monkeypatch) -> None:
    monkeypatch.setattr("app.config.requests.get", lambda url, timeout: FakeResponse())
    for key in list(os.environ):
        if key.startswith("SNAPTRADE_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("SNAPTRADE_OAUTH_METADATA_URL", "https://example.test/.well-known")

    settings = load_settings()

    assert settings.oauth_metadata_url == "https://example.test/.well-known"
    assert settings.device_authorization_url == "https://example.test/device"
    assert settings.token_url == "https://example.test/token"
    assert settings.revoke_url == "https://example.test/revoke"


def test_load_settings_accepts_display_rotation(monkeypatch) -> None:
    for key in list(os.environ):
        if key.startswith("SNAPTRADE_") or key == "DISPLAY_ROTATION":
            monkeypatch.delenv(key)
    monkeypatch.setenv("DISPLAY_ROTATION", "180")

    settings = load_settings()

    assert settings.display_rotation == 180


def test_load_settings_accepts_display_theme(monkeypatch) -> None:
    for key in list(os.environ):
        if key.startswith("SNAPTRADE_") or key == "DISPLAY_THEME":
            monkeypatch.delenv(key)
    monkeypatch.setenv("DISPLAY_THEME", "dark")

    settings = load_settings()

    assert settings.display_theme == "dark"


def test_load_settings_rejects_invalid_display_theme(monkeypatch) -> None:
    for key in list(os.environ):
        if key.startswith("SNAPTRADE_") or key == "DISPLAY_THEME":
            monkeypatch.delenv(key)
    monkeypatch.setenv("DISPLAY_THEME", "midnight")

    try:
        load_settings()
    except ValueError as exc:
        assert "DISPLAY_THEME" in str(exc)
        return
    raise AssertionError("expected ValueError")


def test_load_settings_rejects_invalid_display_rotation(monkeypatch) -> None:
    for key in list(os.environ):
        if key.startswith("SNAPTRADE_") or key == "DISPLAY_ROTATION":
            monkeypatch.delenv(key)
    monkeypatch.setenv("DISPLAY_ROTATION", "90")

    try:
        load_settings()
    except ValueError as exc:
        assert "DISPLAY_ROTATION" in str(exc)
        return
    raise AssertionError("expected ValueError")
