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
    def __init__(self, payload, authorizations=None):
        self.payload = payload
        self.authorizations = authorizations if authorizations is not None else []
        self.requested_urls = []
        self.requested_headers = None

    def get(self, url, headers, timeout):
        self.requested_urls.append(url)
        self.requested_headers = headers
        if url.endswith("/authorizations"):
            return FakeResponse(self.authorizations)
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

    assert session.requested_urls == [
        "https://api.snaptrade.test/accounts",
        "https://api.snaptrade.test/authorizations",
    ]
    assert session.requested_headers == {"Authorization": "Bearer token"}
    assert summary.total == Decimal("125.50")
    assert summary.partial is True
    assert summary.skipped_items == 2
    assert summary.disabled_connections == 0
    assert summary.connection_count == 0


def test_fetch_portfolio_summary_counts_disabled_connections() -> None:
    session = FakeSession(
        [{"balance": {"total": {"amount": 100, "currency": "USD"}}}],
        authorizations=[
            {"id": "auth-1", "disabled": False},
            {"id": "auth-2", "disabled": True},
            {"id": "auth-3", "status": "DISABLED"},
            {"id": "auth-4", "status": "ACTIVE"},
        ],
    )
    client = SnapTradeClient("https://api.snaptrade.test", session=session)

    summary = client.fetch_portfolio_summary(
        TokenSet(access_token="token", refresh_token=None, expires_at=9999999999),
        "USD",
    )

    assert summary.disabled_connections == 2
    assert summary.connection_count == 4


def test_fetch_account_debug_rows_explains_skipped_accounts() -> None:
    session = FakeSession(
        [
            {
                "id": "acct-1",
                "name": "Taxable",
                "institutionName": "Broker A",
                "balance": {"total": {"amount": 100, "currency": "USD"}},
            },
            {
                "id": "acct-2",
                "name": "TFSA",
                "institutionName": "Broker B",
                "balance": {"total": {"amount": "25.50", "currency": "CAD"}},
            },
            {
                "id": "acct-3",
                "name": "Retirement",
                "institutionName": "Broker C",
                "balance": {},
            },
        ]
    )
    client = SnapTradeClient("https://api.snaptrade.test", session=session)

    rows = client.fetch_account_debug_rows(
        TokenSet(access_token="token", refresh_token=None, expires_at=9999999999),
        "USD",
    )

    assert rows[0].name == "Taxable"
    assert rows[0].institution == "Broker A"
    assert rows[0].included is True
    assert rows[0].reason == "included"
    assert rows[1].name == "TFSA"
    assert rows[1].included is False
    assert rows[1].reason == "currency mismatch"
    assert rows[2].name == "Retirement"
    assert rows[2].included is False
    assert rows[2].reason == "missing balance"
