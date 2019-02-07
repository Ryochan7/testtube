import os
import multiprocessing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

raw_env = "DJANGO_SETTINGS_MODULE=testtube.settings.prod"
bind = "unix:/tmp/testtube.sock"
workers = multiprocessing.cpu_count() * 2 + 1
accesslog = os.path.join(BASE_DIR, "log", "gunicorn-access.log")
errorlog = os.path.join(BASE_DIR, "log", "gunicorn-error.log")

