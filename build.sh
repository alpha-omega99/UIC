#!/usr/bin/env bash
# Build Render : installe, collecte les statiques, migre, crée la table de cache
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py createcachetable
python manage.py check --deploy --fail-level ERROR

# --- Offre gratuite (pas de Shell) : initialisation automatique, sans écraser les données existantes ---
# Contenu de départ : seulement si la base est vide.
python manage.py shell -c "
from apps.filieres.models import Filiere
from django.core.management import call_command
if not Filiere.objects.exists():
    call_command('seed_uic')
    print('Contenu initial chargé.')
else:
    print('Contenu déjà présent : seed ignoré.')
"
# Images du site (static/img) : associées sans écraser les choix faits dans l'administration.
python manage.py seed_images

# Administrateur : créé seulement si les 3 variables existent et que le compte n'existe pas encore.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]; then
  python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
U = get_user_model()
n = os.environ['DJANGO_SUPERUSER_USERNAME']
if not U.objects.filter(username=n).exists():
    U.objects.create_superuser(n, os.environ['DJANGO_SUPERUSER_EMAIL'], os.environ['DJANGO_SUPERUSER_PASSWORD'])
    print('Administrateur créé.')
else:
    print('Administrateur déjà existant.')
"
fi
