# SnapTrade Pi

A small Raspberry Pi e-paper display for your SnapTrade portfolio total. Pair it with your own SnapTrade account using device-code OAuth; the app requests read access and cannot place trades. Tokens stay on the Pi in a file readable only by its owner.

The reference build uses a Raspberry Pi Zero W, a Waveshare 2.13-inch black-and-white V4 e-Paper HAT (250 × 122), and Raspberry Pi OS Lite 32-bit. The app also runs without display hardware and writes a PNG preview.

## Build your own

The [build guide](https://pi.snaptra.de/build) has the parts list, assembly photos, and a downloadable DIY kit with the installer. The installer pins the Waveshare driver and configures a systemd service. It matches the working reference device, but has not yet been validated on a freshly flashed SD card.

The production kit uses a public OAuth client ID, which requires no client secret or developer API key. Configure the display in `.env` after installation. Common settings are `DISPLAY_THEME=dark` or `light`, `DISPLAY_ROTATION=180` or `0`, `DISPLAY_CURRENCY=USD`, and `REFRESH_INTERVAL_SECONDS=900`. Only balances already in the selected currency are totaled; the app does not convert currencies.

## Develop locally

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python -m app.mock_server
```

In another shell, activate the same virtual environment and run `python -m app.main --once`. The mock server supplies a local pairing flow and sample portfolio. The generated preview is at `/tmp/snaptrade-portfolio-display.png`. Run `python scripts/display-test.py` for a display-only preview.

The checked-in `.env.example` is for local mock mode. `distribution/production.env.example` holds the production defaults used by the DIY kit. Never commit `.env`, token files, or account data.

## Project layout

- `app/`: OAuth flow, portfolio aggregation, and e-paper rendering
- `distribution/`: public DIY installer and production settings template
- `scripts/package-diy.py`: builds a source ZIP from an explicit file allowlist
- `tests/`: focused unit tests
- `systemd/`: reference service unit for the original device

To run the tests and style check:

```sh
python -m pytest
python -m ruff check .
```

If a brokerage connection is disabled, reconnect it through the [SnapTrade dashboard](https://dashboard.snaptrade.com/). The `partial` indicator means some balances were omitted, such as accounts in another currency. The `stale` indicator means a refresh failed and the last image remains visible.

## License

The software is available under the [MIT License](LICENSE). SnapTrade names and logos are not licensed for reuse by this software license. The Waveshare driver is downloaded separately from its upstream project during installation.
