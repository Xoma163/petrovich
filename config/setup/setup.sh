#!/bin/bash
# install python, python-venv and project requirements
sudo apt -y update
sudo apt install -y python3.7 python3.7-venv python3-venv python3.7-dev python3-wheel postgresql libpq-dev ffmpeg nginx build-essential python-opencv awscli

python3.7 -m venv venv
set -e
source ./venv/bin/activate
pip install wheel
pip install --upgrade pip setuptools wheel virtualenv
pip install -r requirements.txt

# rename abs paths
old_path="/var/www/petrovich/"
sed -i "s#$old_path#$PWD/#g" ./config/petrovich.service
sed -i "s#$old_path#$PWD/#g" ./config/petrovich_site.service
sed -i "s#$old_path#$PWD/#g" ./config/petrovich_nginx.conf

#amazon config
cp ./config/amazon/config ~/.aws/config
cp ./config/amazon/creditionals ~/.aws/creditionals

# systemd
rm /etc/systemd/system/petrovich.service || echo $
rm /etc/systemd/system/petrovich_site.service || echo $
sudo ln -s "$PWD/config/petrovich.service" /etc/systemd/system/ || echo $
sudo ln -s "$PWD/config/petrovich_site.service" /etc/systemd/system/ || echo $
sudo systemctl daemon-reload

# web
rm /etc/nginx/sites-available/petrovich_nginx.conf || echo $
rm /etc/nginx/sites-enabled/petrovich_nginx.conf || echo $
sudo ln -s "$PWD/config/petrovich_nginx.conf" /etc/nginx/sites-available/ || echo $
sudo ln -s "$PWD/config/petrovich_nginx.conf" /etc/nginx/sites-enabled/ || echo $
sudo systemctl restart nginx

# migrations
python manage.py migrate
python manage.py initial
