from __future__ import annotations

from typing import Any

import requests

from app.portfolio import PortfolioSummary, aggregate_portfolio
from app.token_store import TokenSet


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
        return aggregate_portfolio(items, display_currency)

    def revoke(self, revoke_url: str, tokens: TokenSet) -> None:
        self.session.post(
            revoke_url,
            data={"token": tokens.refresh_token or tokens.access_token},
            timeout=10,
        ).raise_for_status()


def _account_balance_item(account: dict[str, Any]) -> dict[str, Any]:
    total = account.get("balance", {}).get("total", {})
    if not isinstance(total, dict):
        total = {}
    return {
        "value": total.get("amount"),
        "currency": total.get("currency"),
    }
