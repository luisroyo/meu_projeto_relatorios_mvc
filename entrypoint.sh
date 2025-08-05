#!/bin/bash
set -e

# Aplica migrations
flask db upgrade

# Inicia o Gunicorn apontando para a app factory
exec gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --timeout 120
