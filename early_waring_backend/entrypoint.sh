#!/bin/bash
set -e

echo "=== Applying migrations... ==="
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "=== Collecting static files... ==="
python manage.py collectstatic --noinput

echo "=== Seeding data... ==="
python manage.py seed_data

echo "=== Starting Gunicorn... ==="
exec gunicorn early_waring_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-level info
