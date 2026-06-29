from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import logging
from typing import Any

import requests

from app.portfolio import PortfolioSummary, aggregate_portfolio
from app.token_store import TokenSet


LOG = logging.getLogger("snaptrade-portfolio-display")


@dataclass(frozen=True)
class AccountDebugRow:
    name: str
    account_id: str | None
    institution: str | None
    value: Decimal | None
    currency: str | None
    included: bool
    reason: str


class SnapTradeClient:
    def __init__(self, api_base_url: str, session: requests.Session | None = None) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.session = session or requests.Session()

    def fetch_portfolio_summary(
        self, tokens: TokenSet, display_currency: str
    ) -> PortfolioSummary:
        headers = {"Authorization": f"{tokens.token_type} {tokens.access_token}"}
        response = self.session.get(
            f"{self.api_base_url}/accounts",
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        payload: Any = response.json()
        if not isinstance(payload, list):
            payload = []
        items = [_account_balance_item(account) for account in payload if isinstance(account, dict)]
        summary = aggregate_portfolio(items, display_currency)
        disabled_connections, connection_count = self._fetch_connection_counts(headers)
        return PortfolioSummary(
            total=summary.total,
            currency=summary.currency,
            partial=summary.partial,
            skipped_items=summary.skipped_items,
            disabled_connections=disabled_connections,
            connection_count=connection_count,
        )

    def fetch_account_debug_rows(
        self, tokens: TokenSet, display_currency: str
    ) -> list[AccountDebugRow]:
        headers = {"Authorization": f"{tokens.token_type} {tokens.access_token}"}
        response = self.session.get(
            f"{self.api_base_url}/accounts",
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        payload: Any = response.json()
        if not isinstance(payload, list):
            return []
        return [
            _account_debug_row(account, display_currency)
            for account in payload
            if isinstance(account, dict)
        ]

    def revoke(self, revoke_url: str, tokens: TokenSet) -> None:
        self.session.post(
            revoke_url,
            data={"token": tokens.refresh_token or tokens.access_token},
            timeout=10,
        ).raise_for_status()

    def _fetch_connection_counts(self, headers: dict[str, str]) -> tuple[int | None, int | None]:
        try:
            response = self.session.get(
                f"{self.api_base_url}/authorizations",
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            LOG.warning("failed to fetch SnapTrade authorizations: %s", exc)
            return None, None

        payload: Any = response.json()
        if not isinstance(payload, list):
            return None, None
        authorizations = [item for item in payload if isinstance(item, dict)]
        disabled = sum(1 for authorization in authorizations if _authorization_is_disabled(authorization))
        return disabled, len(authorizations)


def _account_balance_item(account: dict[str, Any]) -> dict[str, Any]:
    total = account.get("balance", {}).get("total", {})
    if not isinstance(total, dict):
        total = {}
    return {
        "value": total.get("amount"),
        "currency": total.get("currency"),
    }


def _account_debug_row(account: dict[str, Any], display_currency: str) -> AccountDebugRow:
    item = _account_balance_item(account)
    currency = item.get("currency")
    value = _decimal(item.get("value"))
    if value is None:
        included = False
        reason = "missing balance"
    elif currency != display_currency:
        included = False
        reason = "currency mismatch"
    else:
        included = True
        reason = "included"

    return AccountDebugRow(
        name=_account_name(account),
        account_id=_first_string(account, "id", "accountId", "number"),
        institution=_institution_name(account),
        value=value,
        currency=str(currency) if currency else None,
        included=included,
        reason=reason,
    )


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _account_name(account: dict[str, Any]) -> str:
    return _first_string(account, "name", "accountName", "nickname") or "Unknown account"


def _institution_name(account: dict[str, Any]) -> str | None:
    direct = _first_string(account, "institutionName", "institution_name", "brokerageName")
    if direct:
        return direct
    institution = account.get("institution")
    if isinstance(institution, dict):
        return _first_string(institution, "name", "institutionName")
    brokerage_authorization = account.get("brokerageAuthorization")
    if isinstance(brokerage_authorization, dict):
        return _first_string(brokerage_authorization, "name", "brokerageName")
    return None


def _first_string(account: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = account.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _authorization_is_disabled(authorization: dict[str, Any]) -> bool:
    for key in ("disabled", "is_disabled", "isDisabled"):
        value = authorization.get(key)
        if isinstance(value, bool):
            return value

    status = _first_string(authorization, "status", "connection_status", "connectionStatus")
    if status and status.strip().lower() in {"disabled", "inactive", "deleted"}:
        return True

    return any(
        authorization.get(key) is not None
        for key in ("disabled_at", "disabledAt", "disabled_date", "disabledDate")
    )
