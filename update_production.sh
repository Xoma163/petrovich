#!/bin/bash
git checkout master
git reset HEAD --hard
git clean -fd
git pull

set -a
source .venv/bin/activate
set +a

uv sync

python manage.py migrate
python manage.py collectstatic --noinput

deactivate

sudo systemctl restart petrovich

