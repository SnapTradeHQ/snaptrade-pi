from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime

from app.config import load_settings
from app.display import PortfolioDisplay
from app.oauth_device_flow import (
    AuthorizationDenied,
    AuthorizationExpired,
    DeviceFlowClient,
    TokenRefreshError,
)
from app.snaptrade_client import SnapTradeClient
from app.token_store import TokenSet, TokenStore
from app.wifi_status import is_network_available


LOG = logging.getLogger("snaptrade-portfolio-display")


def pair_device(display: PortfolioDisplay, oauth: DeviceFlowClient, store: TokenStore) -> TokenSet:
    authorization = oauth.start()
    LOG.info(
        "pairing required: open %s and enter code %s",
        authorization.verification_uri,
        authorization.user_code,
    )
    display.render_pairing(authorization.verification_uri_complete, authorization.user_code)
    tokens = oauth.poll_until_complete(
        authorization,
        on_waiting=lambda auth, _remaining: display.render_pairing(
            auth.verification_uri_complete,
            auth.user_code,
        ),
    )
    store.save(tokens)
    return tokens


def get_valid_tokens(
    display: PortfolioDisplay,
    oauth: DeviceFlowClient,
    store: TokenStore,
) -> TokenSet:
    tokens = store.load()
    if tokens is None:
        return pair_device(display, oauth, store)
    if not tokens.is_expired:
        return tokens

    try:
        refreshed = oauth.refresh(tokens)
    except TokenRefreshError:
        store.delete()
        return pair_device(display, oauth, store)

    store.save(refreshed)
    return refreshed


def run_once() -> None:
    settings = load_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    display = PortfolioDisplay(settings.output_preview_path, rotation=settings.display_rotation)
    store = TokenStore(settings.token_path)
    oauth = DeviceFlowClient(
        settings.device_authorization_url,
        settings.token_url,
        settings.client_id,
        settings.scopes,
    )
    client = SnapTradeClient(settings.api_base_url)

    display.render_boot()
    if not settings.is_mock and not is_network_available():
        display.render_wifi_unavailable()
        return

    tokens = get_valid_tokens(display, oauth, store)

    display.render_fetching()
    summary = client.fetch_portfolio_summary(tokens, settings.display_currency)
    display.render_connected(summary, datetime.now())


def run_forever() -> None:
    settings = load_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    display = PortfolioDisplay(settings.output_preview_path, rotation=settings.display_rotation)
    store = TokenStore(settings.token_path)
    oauth = DeviceFlowClient(
        settings.device_authorization_url,
        settings.token_url,
        settings.client_id,
        settings.scopes,
    )
    client = SnapTradeClient(settings.api_base_url)
    last_summary = None
    last_updated_at = None

    while True:
        try:
            if not settings.is_mock and not is_network_available():
                if last_summary and last_updated_at:
                    display.render_connected(last_summary, last_updated_at, stale=True, error_message="Wi-Fi error")
                else:
                    display.render_wifi_unavailable()
                time.sleep(settings.refresh_interval_seconds)
                continue

            try:
                tokens = get_valid_tokens(display, oauth, store)
            except (AuthorizationDenied, AuthorizationExpired):
                store.delete()
                display.render_reconnect_needed()
                time.sleep(settings.refresh_interval_seconds)
                continue

            display.render_fetching()
            last_summary = client.fetch_portfolio_summary(tokens, settings.display_currency)
            last_updated_at = datetime.now()
            display.render_connected(last_summary, last_updated_at)
        except Exception:
            LOG.exception("refresh failed")
            if last_summary and last_updated_at:
                display.render_connected(last_summary, last_updated_at, stale=True, error_message="API error")
            else:
                display.render_reconnect_needed()

        time.sleep(settings.refresh_interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Render one refresh cycle and exit.")
    args = parser.parse_args()
    if args.once:
        run_once()
    else:
        run_forever()


if __name__ == "__main__":
    main()
