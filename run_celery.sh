#!/bin/sh

export DJANGO_SETTINGS_MODULE="testtube.settings.dev"
exec celery worker -A testtube --loglevel=debug --concurrency=1 &

