from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TokenSet:
    access_token: str
    refresh_token: str | None
    expires_at: float
    token_type: str = "Bearer"
    scope: str | None = None

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at - 60

    @classmethod
    def from_oauth_response(cls, payload: dict[str, Any]) -> "TokenSet":
        expires_in = int(payload.get("expires_in", 3600))
        return cls(
            access_token=str(payload["access_token"]),
            refresh_token=payload.get("refresh_token"),
            expires_at=time.time() + expires_in,
            token_type=payload.get("token_type", "Bearer"),
            scope=payload.get("scope"),
        )

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "TokenSet":
        return cls(
            access_token=str(payload["access_token"]),
            refresh_token=payload.get("refresh_token"),
            expires_at=float(payload["expires_at"]),
            token_type=payload.get("token_type", "Bearer"),
            scope=payload.get("scope"),
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
            "scope": self.scope,
        }

    def with_refresh_token(self, refresh_token: str) -> "TokenSet":
        return TokenSet(
            access_token=self.access_token,
            refresh_token=refresh_token,
            expires_at=self.expires_at,
            token_type=self.token_type,
            scope=self.scope,
        )


class TokenStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> TokenSet | None:
        if not self.path.exists():
            return None
        with self.path.open("r", encoding="utf-8") as fh:
            return TokenSet.from_json(json.load(fh))

    def save(self, tokens: TokenSet) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as fh:
            json.dump(tokens.to_json(), fh)
        os.chmod(temp_path, 0o600)
        temp_path.replace(self.path)
        os.chmod(self.path, 0o600)

    def delete(self) -> None:
        self.path.unlink(missing_ok=True)
