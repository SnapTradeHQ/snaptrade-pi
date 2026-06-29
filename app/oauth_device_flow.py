from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

import requests

from app.token_store import TokenSet


DEVICE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
REFRESH_GRANT_TYPE = "refresh_token"


class DeviceFlowError(RuntimeError):
    pass


class AuthorizationDenied(DeviceFlowError):
    pass


class AuthorizationExpired(DeviceFlowError):
    pass


class TokenRefreshError(DeviceFlowError):
    pass


@dataclass(frozen=True)
class DeviceAuthorization:
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int


class DeviceFlowClient:
    def __init__(
        self,
        device_authorization_url: str,
        token_url: str,
        client_id: str,
        scopes: str,
        session: requests.Session | None = None,
    ) -> None:
        self.device_authorization_url = device_authorization_url
        self.token_url = token_url
        self.client_id = client_id
        self.scopes = scopes
        self.session = session or requests.Session()

    def start(self) -> DeviceAuthorization:
        response = self.session.post(
            self.device_authorization_url,
            data={"client_id": self.client_id, "scope": self.scopes},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        return DeviceAuthorization(
            device_code=payload["device_code"],
            user_code=payload["user_code"],
            verification_uri=payload["verification_uri"],
            verification_uri_complete=payload.get(
                "verification_uri_complete", payload["verification_uri"]
            ),
            expires_in=int(payload.get("expires_in", 900)),
            interval=int(payload.get("interval", 5)),
        )

    def poll_once(self, authorization: DeviceAuthorization) -> TokenSet | str:
        response = self.session.post(
            self.token_url,
            data={
                "grant_type": DEVICE_GRANT_TYPE,
                "device_code": authorization.device_code,
                "client_id": self.client_id,
            },
            timeout=10,
        )
        payload = response.json()
        if response.ok and "access_token" in payload:
            return TokenSet.from_oauth_response(payload)

        error = payload.get("error")
        if error == "authorization_pending":
            return "authorization_pending"
        if error == "slow_down":
            return "slow_down"
        if error == "access_denied":
            raise AuthorizationDenied("device authorization was denied")
        if error == "expired_token":
            raise AuthorizationExpired("device authorization expired")

        response.raise_for_status()
        raise DeviceFlowError(f"unexpected device-flow response: {error or payload}")

    def poll_until_complete(
        self,
        authorization: DeviceAuthorization,
        on_waiting: Callable[[DeviceAuthorization, int], None] | None = None,
    ) -> TokenSet:
        deadline = time.time() + authorization.expires_in
        interval = authorization.interval

        while time.time() < deadline:
            result = self.poll_once(authorization)
            if isinstance(result, TokenSet):
                return result
            if result == "slow_down":
                interval += 5
            if on_waiting:
                on_waiting(authorization, max(0, int(deadline - time.time())))
            time.sleep(interval)

        raise AuthorizationExpired("device authorization expired")

    def refresh(self, tokens: TokenSet) -> TokenSet:
        if not tokens.refresh_token:
            raise TokenRefreshError("no refresh token is available")

        response = self.session.post(
            self.token_url,
            data={
                "grant_type": REFRESH_GRANT_TYPE,
                "refresh_token": tokens.refresh_token,
                "client_id": self.client_id,
            },
            timeout=10,
        )
        payload = response.json()
        if response.ok and "access_token" in payload:
            refreshed = TokenSet.from_oauth_response(payload)
            if refreshed.refresh_token is None:
                refreshed = refreshed.with_refresh_token(tokens.refresh_token)
            return refreshed

        error = payload.get("error")
        if error in {"invalid_grant", "invalid_request", "invalid_client"}:
            raise TokenRefreshError(f"token refresh failed: {error}")

        response.raise_for_status()
        raise TokenRefreshError(f"unexpected token refresh response: {error or payload}")
