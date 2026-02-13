#!/usr/bin/env bash
# exit on error
set -o errexit

npm install
npm run build --prefix frontend

pip install -r backend/requirements.txt
# Ensure Flask runs from backend/
# You can set this as the Build Command in Render: ./build.sh
# And Start Command: ./backend/entrypoint.sh
