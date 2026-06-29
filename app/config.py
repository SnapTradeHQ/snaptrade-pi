from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import requests
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    env: str
    client_id: str
    scopes: str
    oauth_metadata_url: str | None
    device_authorization_url: str
    token_url: str
    revoke_url: str | None
    api_base_url: str
    display_currency: str
    display_rotation: int
    refresh_interval_seconds: int
    token_path: Path
    output_preview_path: Path

    @property
    def is_mock(self) -> bool:
        return self.env == "mock"


def load_settings(env_file: str | Path | None = None) -> Settings:
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    default_token_path = config_dir / "snaptrade-portfolio-display" / "tokens.json"
    oauth_metadata_url = os.environ.get("SNAPTRADE_OAUTH_METADATA_URL")
    metadata = _load_oauth_metadata(oauth_metadata_url) if oauth_metadata_url else {}

    return Settings(
        env=os.environ.get("SNAPTRADE_ENV", "mock"),
        client_id=os.environ.get("SNAPTRADE_CLIENT_ID", "snaptrade-pi-dev"),
        scopes=os.environ.get("SNAPTRADE_SCOPES", "accounts:read holdings:read"),
        oauth_metadata_url=oauth_metadata_url,
        device_authorization_url=os.environ.get(
            "SNAPTRADE_DEVICE_AUTHORIZATION_URL",
            metadata.get(
                "device_authorization_endpoint",
                "http://127.0.0.1:8088/v1/oauth/device_authorization/",
            ),
        ),
        token_url=os.environ.get(
            "SNAPTRADE_TOKEN_URL",
            metadata.get("token_endpoint", "http://127.0.0.1:8088/v1/oauth/token/"),
        ),
        revoke_url=os.environ.get("SNAPTRADE_REVOKE_URL", metadata.get("revocation_endpoint")),
        api_base_url=os.environ.get("SNAPTRADE_API_BASE_URL", "http://127.0.0.1:8088"),
        display_currency=os.environ.get("DISPLAY_CURRENCY", "USD"),
        display_rotation=_load_display_rotation(),
        refresh_interval_seconds=int(os.environ.get("REFRESH_INTERVAL_SECONDS", "900")),
        token_path=Path(os.environ.get("TOKEN_PATH", default_token_path)),
        output_preview_path=Path(
            os.environ.get("OUTPUT_PREVIEW_PATH", "/tmp/snaptrade-portfolio-display.png")
        ),
    )


def _load_display_rotation() -> int:
    rotation = int(os.environ.get("DISPLAY_ROTATION", "0"))
    if rotation not in {0, 180}:
        raise ValueError("DISPLAY_ROTATION must be 0 or 180")
    return rotation


def _load_oauth_metadata(url: str) -> dict[str, str]:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("OAuth metadata response must be a JSON object")
    return {str(key): str(value) for key, value in payload.items() if isinstance(value, str)}
