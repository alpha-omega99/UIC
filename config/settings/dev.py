from .base import *  # noqa

DEBUG = True
if not SECRET_KEY:
    # Clé jetable pour le développement (les sessions sont perdues à chaque redémarrage).
    # Pour une clé fixe, renseigner SECRET_KEY dans .env.
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = get_random_secret_key()
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
STORAGES = {**STORAGES, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
MIDDLEWARE = [m for m in MIDDLEWARE if 'whitenoise' not in m]   # runserver sert déjà les statiques en dev
