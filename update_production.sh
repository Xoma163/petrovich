#!/bin/bash
git checkout master
git reset HEAD --hard
git clean -fd
git pull

#npm run build
venv/bin/python -m pip install --upgrade pip setuptools wheel  | grep -v 'Requirement already satisfied'
venv/bin/pip install -r requirements.txt | grep -v 'Requirement already satisfied'
venv/bin/python manage.py migrate
venv/bin/python manage.py collectstatic --noinput

sudo systemctl restart petrovich
