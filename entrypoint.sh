#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py create_demo_data
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
