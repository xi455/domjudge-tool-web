#!/bin/sh
set -e

echo "Waiting for Database to start...."
python3 manage.py shell < ./wait_database.py

echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Migrating Database"
python3 manage.py migrate

echo "Create admin user"
python3 manage.py createsuperuser --noinput || true

echo "Make log dir"
[[ -d ./log/archived ]] || mkdir -p ./log/archived

echo "Run crontab"
crond

echo "Start uwsgi"
uwsgi --ini uwsgi.ini
