from __future__ import annotations

import logging
import sys
from decimal import Decimal

from app.config import load_settings
from app.oauth_device_flow import DeviceFlowClient, TokenRefreshError
from app.snaptrade_client import AccountDebugRow, SnapTradeClient
from app.token_store import TokenStore


LOG = logging.getLogger("snaptrade-portfolio-display")


def _format_value(value: Decimal | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def _format_account(row: AccountDebugRow) -> str:
    institution = f"{row.institution} / " if row.institution else ""
    account_id = f" ({row.account_id})" if row.account_id else ""
    return f"{institution}{row.name}{account_id}"


def print_account_debug(rows: list[AccountDebugRow]) -> None:
    account_width = min(
        max([len("Account"), *(len(_format_account(row)) for row in rows)], default=7),
        48,
    )
    print(
        f"{'Account':<{account_width}}  {'Currency':<8}  {'Value':>14}  Status"
    )
    print(
        f"{'-' * account_width}  {'-' * 8}  {'-' * 14}  {'-' * 24}"
    )
    for row in rows:
        account = _format_account(row)
        if len(account) > account_width:
            account = f"{account[: account_width - 3]}..."
        print(
            f"{account:<{account_width}}  "
            f"{row.currency or '-':<8}  "
            f"{_format_value(row.value):>14}  "
            f"{row.reason}"
        )


def main() -> None:
    settings = load_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    store = TokenStore(settings.token_path)
    oauth = DeviceFlowClient(
        settings.device_authorization_url,
        settings.token_url,
        settings.client_id,
        settings.scopes,
    )
    client = SnapTradeClient(settings.api_base_url)
    tokens = store.load()
    if tokens is None:
        sys.exit(
            f"No saved token found at {settings.token_path}. "
            "Pair the display before debugging accounts."
        )
    if tokens.is_expired:
        try:
            tokens = oauth.refresh(tokens)
        except TokenRefreshError as exc:
            sys.exit(f"Saved token is expired and refresh failed: {exc}")
        store.save(tokens)
    rows = client.fetch_account_debug_rows(tokens, settings.display_currency)
    print_account_debug(rows)


if __name__ == "__main__":
    main()
