#!/bin/bash
git checkout master
git reset HEAD --hard
git clean -fd
git pull

set -a
source venv/bin/activate
set +a

python -m pip install --upgrade pip setuptools wheel  | grep -v 'Requirement already satisfied'
poetry lock
poetry install # venv/bin/pip install -r requirements.txt | grep -v 'Requirement already satisfied'
python manage.py migrate
python manage.py collectstatic --noinput

sudo systemctl restart petrovich

deactivate