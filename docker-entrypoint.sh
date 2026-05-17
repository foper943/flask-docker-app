#!/bin/sh
set -e

echo "Применение миграций..."
python cli.py migrate

echo "Запуск сервера..."
exec gunicorn --config gunicorn.conf.py run:app
