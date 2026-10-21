"""
UIC — Paramètres communs. dev.py / prod.py en héritent.
Aucune valeur secrète ici : tout vient de l'environnement (.env).
"""
from pathlib import Path
import environ
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# ── Sécurité de base ─────────────────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY', default='').strip()   # vide = refusé en production, clé jetable en dev
DEBUG = env.bool('DEBUG', default=False)       # False par défaut = sûr
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
ADMIN_URL = env('ADMIN_URL', default='gestion-uic/')

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'apps.core', 'apps.filieres', 'apps.actualites', 'apps.admissions',
    'apps.galerie', 'apps.professeurs', 'apps.contact', 'apps.portail',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csp.ContentSecurityPolicyMiddleware',
    'config.middleware.ExtraSecurityHeadersMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'apps.core.context_processors.site_context',
    ]},
}]

# ── Base de données : PostgreSQL si DATABASE_URL est défini, sinon SQLite ────
if env('DATABASE_URL', default=''):
    DATABASES = {'default': env.db('DATABASE_URL')}
    DATABASES['default']['CONN_MAX_AGE'] = 60
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': env('SQLITE_PATH', default=str(BASE_DIR / 'db.sqlite3')),
    }}

# Cache partagé entre workers (sert au rate limiting) — table créée par createcachetable
CACHES = {'default': {
    'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
    'LOCATION': 'uic_cache',
}}
RATELIMIT_USE_CACHE = 'default'
SILENCED_SYSTEM_CHECKS = ['django_ratelimit.E003', 'django_ratelimit.W001']  # cache DB partagé, suffisant ici

# ── Mots de passe ────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# ── I18N ─────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

# ── Fichiers ─────────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'                                              # images publiques (filières, articles, galerie…)
MEDIA_ROOT = env('MEDIA_ROOT', default=str(BASE_DIR / 'media'))
PRIVATE_MEDIA_ROOT = env('PRIVATE_MEDIA_ROOT', default=str(BASE_DIR / 'private_media'))  # documents étudiants : JAMAIS publics
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
DATA_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024        # 1 Mo pour les formulaires publics (aucun upload public)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 200

# ── Auth / portail ───────────────────────────────────────────────────────────
LOGIN_URL = '/portail/connexion/'
LOGIN_REDIRECT_URL = '/portail/tableau-de-bord/'
LOGOUT_REDIRECT_URL = '/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 60 * 60 * 8
SESSION_SAVE_EVERY_REQUEST = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False   # le token est lu dans le DOM ; cookie non-HttpOnly reste le comportement Django standard
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ── Content-Security-Policy (aucun script inline autorisé) ───────────────────
SECURE_CSP = {
    'default-src': [CSP.SELF],
    'script-src': [CSP.SELF],
    'style-src': [CSP.SELF, CSP.UNSAFE_INLINE, 'https://fonts.googleapis.com'],  # le design utilise des styles inline
    'font-src': [CSP.SELF, 'https://fonts.gstatic.com'],
    'img-src': [CSP.SELF, 'data:', 'https://images.unsplash.com'],
    'frame-src': ['https://www.google.com'],                                      # carte Google Maps (contact)
    'connect-src': [CSP.SELF],
    'object-src': [CSP.NONE],
    'base-uri': [CSP.SELF],
    'form-action': [CSP.SELF],
    'frame-ancestors': [CSP.NONE],
}

# ── E-mail ───────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='UIC <uicinfos@gmail.com>')
BREVO_API_KEY = env('BREVO_API_KEY', default='')   # option HTTPS (hébergement gratuit Render)
NOTIFY_EMAIL = env('NOTIFY_EMAIL', default='uicinfos@gmail.com')
EMAIL_TIMEOUT = 10

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
