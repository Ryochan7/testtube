from common import *

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
