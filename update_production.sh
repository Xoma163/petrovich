#!/bin/bash
set -euo pipefail

git checkout master
git reset HEAD --hard
git clean -fd
git pull

source .venv/bin/activate

uv sync

python manage.py migrate --noinput
python manage.py collectstatic --noinput

deactivate

sudo systemctl restart petrovich
