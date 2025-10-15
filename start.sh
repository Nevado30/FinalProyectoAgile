#!/usr/bin/env bash
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python -m gunicorn baseParcial.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
