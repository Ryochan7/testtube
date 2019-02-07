#!/bin/sh

exec gunicorn --config gunicorn.conf.py testtube.wsgi &

