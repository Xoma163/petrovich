#!/bin/bash
git checkout master
git reset HEAD --hard
git clean -fd
git pull

source venv/bin/activate

python -m pip install --upgrade pip setuptools wheel  | grep -v 'Requirement already satisfied'
poetry install # venv/bin/pip install -r requirements.txt | grep -v 'Requirement already satisfied'
python manage.py migrate
python manage.py collectstatic --noinput

sudo systemctl restart petrovich

deactivate