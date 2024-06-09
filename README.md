# testtube

Prototype video sharing site made in Django

![Testtube Preview](https://raw.githubusercontent.com/Ryochan7/testtube/master/testtube_preview.png)

## Setup

### Extra Non-Python Dependencies

* ffmpeg
* redis
* nginx (optional)

### Starting

It is recommended that this project be run in its own Python
virtual environment.

Set up virtual environment:

```
python -m venv testtube-env
cd testtube-env
source bin/activate
```

Download project code:
```
git clone https://github.com/Ryochan7/testtube.git
```

Development setup commands:

```
cd testtube
pip install -r reqs/dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The program **celery** needs to be running in a separate terminal
since it will handle launching ffmpeg to encode video files.
Before launching celery, make sure to activate the testtube-env virtual
environment from within that terminal. Also, it has to be launched
from the main project folder. Example:

```
celery -A testtube worker --loglevel=debug --concurrency=1
```
