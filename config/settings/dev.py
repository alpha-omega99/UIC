from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
STORAGES = {**STORAGES, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m]   # runserver sert déjà les statiques en dev
