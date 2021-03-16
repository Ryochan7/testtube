#!/bin/sh

export DJANGO_SETTINGS_MODULE="testtube.settings.dev"
exec celery -A testtube worker --loglevel=debug --concurrency=1 &

