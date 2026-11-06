#!/bin/sh
set -eu
python -m flask --app app:create_app db upgrade
exec gunicorn --bind "0.0.0.0:${PORT:-5000}" --workers 2 --access-logfile - "app:create_app()"
