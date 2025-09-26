#!/bin/bash
set -e

# Print environment variables for debugging
echo "=== Environment Variables ==="
printenv | sort
echo "==========================="

# Change to the app directory
cd /app

# Run prestart script if it exists
if [ -f /app/prestart.sh ]; then
    echo "Running prestart script..."
    . /app/prestart.sh
else
    echo "No prestart script found at /app/prestart.sh"
fi

# Run database migrations if manage.py exists
if [ -f /app/manage.py ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
fi

# Collect static files if manage.py exists
if [ -f /app/manage.py ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

# Start the Gunicorn server
exec "$@"
