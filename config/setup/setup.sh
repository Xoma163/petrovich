#!/bin/bash
# install python and system depends
sudo apt -y update
curl -LsSf https://astral.sh/uv/install.sh | sh

sudo apt install -y libpq-dev gcc python3-dev redis ffmpeg chromium chromium-driver

# venv and python depends
# Создаём виртуальное окружение через uv.
uv venv .venv
set -e
source ./.venv/bin/activate
uv sync

# migrations and init db
python manage.py migrate
python manage.py initial
