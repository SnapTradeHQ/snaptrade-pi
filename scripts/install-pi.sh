#!/usr/bin/env sh
set -eu

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install spidev RPi.GPIO gpiozero lgpio

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Install complete. Edit .env, then install systemd/snaptrade-portfolio-display.service."
