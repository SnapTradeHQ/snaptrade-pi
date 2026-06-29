# SnapTrade Portfolio Display

Prototype Raspberry Pi desk display for a SnapTrade user's connected portfolio value.

Target hardware:

- Raspberry Pi Zero 2 W with pre-soldered headers
- Waveshare 2.13-inch black/white e-Paper HAT, 250 x 122
- Raspberry Pi OS Lite, Wi-Fi preconfigured through Raspberry Pi Imager

The app is written to run without the display hardware during development. When the Waveshare
Python package is unavailable, it writes a PNG preview to `OUTPUT_PREVIEW_PATH`.

## Local Development

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Start the local mock OAuth/API server:

```sh
python -m app.mock_server
```

In another shell, run one display cycle:

```sh
python -m app.main --once
```

The first run enters pairing mode. Open the approval URL embedded in the generated QR code, or
use the app log line:

```text
pairing required: open http://127.0.0.1:8088/approve and enter code ABC123
```

For mock mode, the complete approval URL is also embedded in the QR preview at
`/tmp/snaptrade-portfolio-display.png`.

To debug why the footer says `partial`, run:

```sh
python -m app.debug_accounts
```

The command reads the saved display token, fetches accounts, and prints which accounts are
included in or skipped from the displayed total. It does not print OAuth tokens.

If the display footer shows disabled connections, the portfolio total may be stale or incomplete
for those brokerages. Reconnect them at `https://dashboard.snaptrade.com`.

## Configuration

Settings are read from `.env` or environment variables:

```text
SNAPTRADE_ENV=mock
SNAPTRADE_CLIENT_ID=snaptrade-pi-dev
SNAPTRADE_DEVICE_AUTHORIZATION_URL=http://127.0.0.1:8088/v1/oauth/device_authorization/
SNAPTRADE_TOKEN_URL=http://127.0.0.1:8088/v1/oauth/token/
SNAPTRADE_REVOKE_URL=http://127.0.0.1:8088/v1/oauth/revoke_token/
SNAPTRADE_API_BASE_URL=http://127.0.0.1:8088
SNAPTRADE_SCOPES=accounts:read holdings:read
DISPLAY_CURRENCY=USD
REFRESH_INTERVAL_SECONDS=900
```

Tokens are stored at:

```text
~/.config/snaptrade-portfolio-display/tokens.json
```

The token file is written with `0600` permissions. The app does not log token values, refresh
tokens, or device codes.

## Raspberry Pi Install

On the Pi:

```sh
sudo apt update
sudo apt install -y git python3-venv python3-pip python3-pil python3-spidev python3-rpi.gpio python3-numpy fonts-dejavu-core
git clone <repo-url> /home/terry/snaptrade-pi
cd /home/terry/snaptrade-pi
sh scripts/install-pi.sh
```

Edit `.env`, then install the service:

```sh
sudo cp systemd/snaptrade-portfolio-display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now snaptrade-portfolio-display
journalctl -u snaptrade-portfolio-display -f
```

If you are using the Waveshare display, copy the vendor `waveshare_epd` folder into the project for
your HAT revision before starting the service.

## E-Paper Display Test

After enabling SPI and attaching the Waveshare HAT, run:

```sh
python scripts/display-test.py
```

If the Waveshare driver is installed and the display is connected correctly, the e-paper screen
should show a SnapTrade test portfolio value. If the driver is missing, the script still writes a
PNG preview to `/tmp/snaptrade-display-test.png`.

## Current Scope

Implemented:

- Device-code OAuth polling state machine
- Local mock OAuth/API server
- Local `0600` token storage
- Portfolio aggregation with explicit partial-data handling
- PNG display previews and optional Waveshare hardware rendering
- `systemd` unit for boot-time startup
- Focused unit tests

Still expected before a real SnapTrade run:

- Replace mock URLs with real SnapTrade device-code OAuth endpoints when available
- Confirm the real portfolio endpoint shape and adapt `SnapTradeClient`
- Add access-token refresh once the production token contract is finalized
- Add a physical disconnect/reset button or CLI command
