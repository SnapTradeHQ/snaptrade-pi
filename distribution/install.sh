#!/bin/sh
# Run from the extracted download as your normal Raspberry Pi user.
set -eu
if [ "$(id -u)" -eq 0 ]; then
  echo 'Run this script as your normal user, without sudo.' >&2; exit 1
fi
if [ ! -r /proc/device-tree/model ] || ! grep -q 'Raspberry Pi' /proc/device-tree/model; then
  echo 'This installer is for Raspberry Pi OS on a Raspberry Pi.' >&2; exit 1
fi
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "$APP_DIR" in *' '*|*'%'*|*'"'*|*'\\'*) echo 'Extract into a path without spaces, percent signs, quotes, or backslashes.' >&2; exit 1;; esac
APP_USER=$(id -un)
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11 or newer is required"'
if systemctl is-active --quiet snaptrade-portfolio-display; then
  echo 'A display service is already running. Stop it before installing an update.' >&2; exit 1
fi
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip python3-pil python3-spidev python3-gpiozero python3-lgpio fonts-dejavu-core curl ca-certificates
sudo raspi-config nonint do_spi 0
sudo usermod -a -G gpio,spi "$APP_USER"
python3 -m venv --system-site-packages "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"
# Vendor driver is pinned; no vendor installer is executed.
DRIVER_REV=a794fbc39656b0f93938d1ffb3fdc77eaed9e9fc
mkdir -p "$APP_DIR/waveshare_epd"
for driver in __init__.py epd2in13_V4.py epdconfig.py; do
  curl --fail --show-error --location "https://raw.githubusercontent.com/waveshareteam/e-Paper/$DRIVER_REV/RaspberryPi_JetsonNano/python/lib/waveshare_epd/$driver" -o "$APP_DIR/waveshare_epd/$driver"
done
if [ ! -f "$APP_DIR/.env" ]; then
  (umask 077; cp "$APP_DIR/production.env.example" "$APP_DIR/.env")
fi
UNIT_FILE=$(mktemp)
trap 'rm -f "$UNIT_FILE"' EXIT HUP INT TERM
cat > "$UNIT_FILE" <<UNIT
[Unit]
Description=SnapTrade Portfolio Display
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/python -m app.main
Restart=on-failure
RestartSec=10
UMask=0077

[Install]
WantedBy=multi-user.target
UNIT
sudo install -m 644 "$UNIT_FILE" /etc/systemd/system/snaptrade-portfolio-display.service
sudo systemctl daemon-reload
sudo systemctl enable snaptrade-portfolio-display
printf '\nInstalled. Reboot the Pi to apply SPI and group settings.\nThe display service will start automatically. Scan its QR code to connect.\n'
