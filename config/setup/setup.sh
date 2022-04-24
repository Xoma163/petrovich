#!/bin/bash
# install python, python-venv and project requirements
sudo apt -y update
sudo apt install -y python3.8 python3.8-venv python3-venv python3.8-dev python3-wheel postgresql libpq-dev ffmpeg nginx build-essential python3-opencv awscli uwsgi

python3.8 -m venv venv
set -e
source ./venv/bin/activate
pip install wheel
pip install --upgrade pip setuptools wheel virtualenv
pip install -r requirements.txt

#amazon config
cp ./config/amazon/config ~/.aws/config
cp ./secrets/amazon/credentials ~/.aws/credentials

# systemd
sudo rm /etc/systemd/system/petrovich.service || echo $
sudo rm /etc/systemd/system/petrovich_site.service || echo $
sudo ln -s "$PWD/config/systemd/petrovich.service" /etc/systemd/system/ || echo $
sudo ln -s "$PWD/config/systemd/petrovich_site.service" /etc/systemd/system/ || echo $
sudo systemctl daemon-reload

# web
sudo rm /etc/nginx/sites-available/petrovich_nginx.conf || echo $
sudo rm /etc/nginx/sites-enabled/petrovich_nginx.conf || echo $
sudo rm /etc/nginx/conf/petrovich-default-config.conf || echo $
sudo rm /etc/nginx/conf/petrovich-default-locations.conf || echo $
sudo rm /etc/nginx/conf/andrewsha-ssl.conf || echo $

cp config/nginx/conf/andrewsha-ssl_example.conf config/nginx/conf/andrewsha-ssl.conf
cp config/nginx/conf/petrovich-default-config_example.conf config/nginx/conf/petrovich-default-config.conf
cp config/nginx/conf/petrovich-default-locations_example.conf config/nginx/conf/petrovich-default-locations.conf
cp config/nginx/petrovich_nginx_example.conf config/nginx/petrovich_nginx.conf
cp config/systemd/petrovich_example.service config/systemd/petrovich.service
cp config/systemd/petrovich_site_example.service config/systemd/petrovich_site.service

# rename abs paths
old_path="/var/www/andrewsha/petrovich/"
sed -i "s#$old_path#$PWD/#g" ./config/systemd/petrovich.service
sed -i "s#$old_path#$PWD/#g" ./config/systemd/petrovich_site.service
sed -i "s#$old_path#$PWD/#g" ./config/nginx/petrovich_nginx.conf
sed -i "s#$old_path#$PWD/#g" ./config/nginx/conf/petrovich-default-locations.conf

sudo mkdir /etc/nginx/conf || echo $

sudo ln -s "$PWD/config/nginx/petrovich_nginx.conf" /etc/nginx/sites-available/ || echo $
sudo ln -s "$PWD/config/nginx/petrovich_nginx.conf" /etc/nginx/sites-enabled/ || echo $
sudo ln -s "$PWD/config/nginx/conf/petrovich-default-config.conf" /etc/nginx/conf/ || echo $
sudo ln -s "$PWD/config/nginx/conf/petrovich-default-locations.conf" /etc/nginx/conf/ || echo $
sudo ln -s "$PWD/config/nginx/conf/andrewsha-ssl.conf" /etc/nginx/conf/ || echo $

sudo systemctl restart nginx

# migrations
python manage.py migrate
python manage.py initial
