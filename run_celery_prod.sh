#!/bin/sh

export DJANGO_SETTINGS_MODULE="testtube.settings.prod"
exec celery -A testtube worker --loglevel=debug --concurrency=1 &

