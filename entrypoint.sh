#!/bin/bash

# Exit on error
set -e

echo "Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be ready
while ! pg_isready -h "$DB_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is up - continuing..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist (optional - for first deployment)
# echo "Creating superuser..."
# python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')"

# Collect static files (for production with whitenoise)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting server..."
# For development
# exec python manage.py runserver 0.0.0.0:8000

# For production (using gunicorn)
exec gunicorn libarary.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
