#!/usr/bin/env bash
# Build Render : installe, collecte les statiques, migre, crée la table de cache
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py createcachetable
python manage.py check --deploy --fail-level ERROR
