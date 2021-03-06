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
sed -i "s#$old_path#$PWD/#g" ./config/nginx/petrovich_nginx.conf
sed -i "s#$old_path#$PWD/#g" ./config/nginx/conf/petrovich-default-locations.conf

#amazon config
cp ./config/amazon/config ~/.aws/config
cp ./config/amazon/creditionals ~/.aws/creditionals

# systemd
sudo rm /etc/systemd/system/petrovich.service || echo $
sudo rm /etc/systemd/system/petrovich_site.service || echo $
sudo ln -s "$PWD/config/petrovich.service" /etc/systemd/system/ || echo $
sudo ln -s "$PWD/config/petrovich_site.service" /etc/systemd/system/ || echo $
sudo systemctl daemon-reload

# web
sudo rm /etc/nginx/sites-available/petrovich_nginx.conf || echo $
sudo rm /etc/nginx/sites-enabled/petrovich_nginx.conf || echo $
sudo rm /etc/nginx/conf/petrovich-default-config.conf || echo $
sudo rm /etc/nginx/conf/petrovich-default-locations.conf || echo $
sudo rm /etc/nginx/conf/petrovich-main-domain-ssl.conf || echo $
sudo rm /etc/nginx/conf/petrovich-subdomains-ssl.conf || echo $
sudo ln -s "$PWD/config/nginx/petrovich_nginx.conf" /etc/nginx/sites-available/ || echo $
sudo ln -s "$PWD/config/nginx/petrovich_nginx.conf" /etc/nginx/sites-enabled/ || echo $
sudo ln -s "$PWD/config/nginx/conf/petrovich-default-config.conf" /etc/nginx/conf/ || echo $
sudo ln -s "$PWD/config/nginx/conf/petrovich-default-locations.conf" /etc/nginx/conf/ || echo $
sudo ln -s "$PWD/config/nginx/conf/petrovich-main-domain-ssl.conf" /etc/nginx/conf/ || echo $
sudo ln -s "$PWD/config/nginx/conf/petrovich-subdomains-ssl.conf" /etc/nginx/conf/ || echo $

sudo mkdir /etc/nginx/conf || echo $

sudo systemctl restart nginx

# migrations
python manage.py migrate
python manage.py initial
