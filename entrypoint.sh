#!/bin/bash

# entrypoint.sh

echo "Running database migrations..."
flask db upgrade

echo "Starting app with Gunicorn..."
exec gunicorn --workers 3 --bind 0.0.0.0:$PORT 'app:create_app()' 