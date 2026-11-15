#!/bin/bash
set -euo pipefail

# install python and system depends
sudo apt -y update
curl --proto '=https' --proto-redir '=https' -LsSf https://astral.sh/uv/install.sh | sh

sudo apt install -y libpq-dev gcc python3-dev redis ffmpeg chromium chromium-driver

# venv and python depends
# Создаём виртуальное окружение через uv.
uv venv .venv
set -e
source ./.venv/bin/activate
bash "$(dirname "${BASH_SOURCE[0]}")/sync_dependencies.sh"

# migrations and init db
python manage.py migrate
python manage.py initial
