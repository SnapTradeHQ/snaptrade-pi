# SnapTrade Pi DIY kit

A Raspberry Pi e-paper portfolio display. This source snapshot matches the application running on the reference Raspberry Pi Zero W Rev 1.1, with a Waveshare 2.13-inch black-and-white V4 HAT and Raspberry Pi OS Lite 32-bit (Trixie).

## Build guide

https://pi.snaptra.de/build

## Install

1. Flash Raspberry Pi OS Lite (32-bit) using Raspberry Pi Imager. Set a username, Wi-Fi and SSH access.
2. With power disconnected, fit the Waveshare HAT onto the full 40-pin header. Use the board alignment and mounting holes in the vendor instructions. Use a pre-soldered header if you do not solder.
3. Insert the SD card, connect micro-USB power to PWR IN and connect over SSH.
4. Extract this kit to a NEW folder in your home directory and run `sh install.sh` as your normal user. The script asks for sudo, installs dependencies, enables SPI, downloads a pinned Waveshare driver and enables a service for your username and directory. It preserves an existing .env and stops if the display service is already running.
5. Reboot using `sudo reboot`. Scan the QR code on the display with your phone and approve SnapTrade access.

The default configuration uses the SnapTrade Pi public OAuth client with read scope. There is no client secret. You sign in with your own SnapTrade account and approve your own access. The kit contains no user tokens or account data.

## Settings

Edit .env, then run `sudo systemctl restart snaptrade-portfolio-display`.

- DISPLAY_THEME: dark or light
- DISPLAY_ROTATION: 180 or 0
- DISPLAY_CURRENCY: USD by default; only matching-currency balances are totaled (no FX conversion)
- REFRESH_INTERVAL_SECONDS: 900 (15 minutes)

## Troubleshooting

- Status: `systemctl status snaptrade-portfolio-display --no-pager`
- Recent logs: `journalctl -u snaptrade-portfolio-display -n 50 --no-pager`
- Blank display: verify power, the V4 black-and-white HAT, full header alignment and SPI; reboot after install.
- QR code / reconnect: approve on your phone. Tokens are kept locally in ~/.config/snaptrade-portfolio-display/tokens.json with owner-only permissions.
- Partial: some balances are omitted, such as accounts in another currency.
- Disabled: reconnect the affected brokerage through the SnapTrade dashboard.
- Stale: check Wi-Fi and the update timestamp. E-paper retains the last image without power.

The application and pinned vendor driver match the working reference device. The new installer has not yet been validated from a freshly flashed SD card. This is an early DIY release.

## License

The included application source is licensed under the MIT License in `LICENSE`. SnapTrade names and logos are not licensed for reuse by that software license. The Waveshare driver is downloaded separately from its upstream project.
