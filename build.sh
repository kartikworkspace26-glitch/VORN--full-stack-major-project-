#!/usr/bin/env bash
# VORN — Render Build Script
set -o errexit  # exit on error

# Install Python dependencies
pip install -r requirements.txt

# Collect static files (WhiteNoise handles serving)
python manage.py collectstatic --noinput --clear

# Run database migrations
python manage.py migrate --noinput

# Create a superuser if DJANGO_SUPERUSER_* env vars are set
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser \
    --noinput \
    --username "${DJANGO_SUPERUSER_USERNAME:-admin}" \
    --email "$DJANGO_SUPERUSER_EMAIL" \
  || true  # Don't fail if superuser already exists
fi

echo "✅ VORN build complete — ready to serve!"
