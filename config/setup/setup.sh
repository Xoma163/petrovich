#!/bin/bash
# install python and system depends
sudo apt -y update
sudo apt install -y python3.14 python3.14-venv python3-venv python3.14-dev python3-wheel postgresql libpq-dev ffmpeg nginx build-essential

# venv and python depends
# Создаём виртуальное окружение через uv.
uv venv .venv
set -e
source ./.venv/bin/activate
python -m pip install --upgrade pip uv
uv sync

# migrations and init db
python manage.py migrate
python manage.py initial
