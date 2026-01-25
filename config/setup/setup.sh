#!/bin/bash
# install python and system depends
sudo apt -y update
sudo apt install -y python3.14 python3.14-venv python3-venv python3.14-dev python3-wheel postgresql libpq-dev ffmpeg nginx build-essential uwsgi

# venv and python depends
python3.14 -m venv venv
set -e
source ./venv/bin/activate
pip install wheel
pip install --upgrade pip setuptools wheel virtualenv
pip install -r requirements.txt

# migrations and init db
python manage.py migrate
python manage.py initial
