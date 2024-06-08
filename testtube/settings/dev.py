from .common import *

### Using Django dev server to host media
RESOURCE_PREFIX = ""
STATIC_URL = "{}/static/".format(RESOURCE_PREFIX)
MEDIA_URL = "{}/media/".format(RESOURCE_PREFIX)

### Using nginx to host media
#RESOURCE_PREFIX = "http://127.0.0.1:8080"
#STATIC_URL = "{}/static/".format(RESOURCE_PREFIX)
#MEDIA_URL = "{}/media/".format(RESOURCE_PREFIX)

ENABLE_TOOLBAR = False
