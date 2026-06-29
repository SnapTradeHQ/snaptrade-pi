from decimal import Decimal

from app.snaptrade_client import SnapTradeClient
from app.token_store import TokenSet


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.requested_url = None
        self.requested_headers = None

    def get(self, url, headers, timeout):
        self.requested_url = url
        self.requested_headers = headers
        return FakeResponse(self.payload)


def test_fetch_portfolio_summary_sums_oauth_account_balances() -> None:
    session = FakeSession(
        [
            {"balance": {"total": {"amount": 100, "currency": "USD"}}},
            {"balance": {"total": {"amount": "25.50", "currency": "USD"}}},
            {"balance": {"total": {"amount": 9, "currency": "CAD"}}},
            {"balance": {}},
        ]
    )
    client = SnapTradeClient("https://api.snaptrade.test", session=session)

    summary = client.fetch_portfolio_summary(
        TokenSet(access_token="token", refresh_token=None, expires_at=9999999999),
        "USD",
    )

    assert session.requested_url == "https://api.snaptrade.test/accounts"
    assert session.requested_headers == {"Authorization": "Bearer token"}
    assert summary.total == Decimal("125.50")
    assert summary.partial is True
    assert summary.skipped_items == 2

