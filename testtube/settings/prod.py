from common import *

DEBUG = False
ENABLE_TOOLBAR = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

STATIC_URL = "http://ryochan7.xyz:8000/static/"
MEDIA_URL = "http://ryochan7.xyz:8000/media/"

RUN_CPULIMIT_FFMPEG = True

if not DEBUG and "debug_toolbar" in INSTALLED_APPS:
  INSTALLED_APPS.remove("debug_toolbar")
#elif DEBUG and "debug_toolbar" in INSTALLED_APPS:
#  MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
