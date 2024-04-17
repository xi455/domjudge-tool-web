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

echo "Create group"
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='teacher');" | python manage.py shell

echo "Make log dir"
[ -d ./log/archived ] || mkdir -p ./log/archived

echo "Run crontab"
service cron start

echo "Start uwsgi"
uwsgi --ini uwsgi.ini
