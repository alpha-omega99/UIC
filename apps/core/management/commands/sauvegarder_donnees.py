"""Sauvegarde TOUTE la base (contenu, formations, actualités, pré-inscriptions, messages, comptes) dans un fichier JSON daté.
Fonctionne avec SQLite comme PostgreSQL, sans pg_dump. Restauration : python manage.py loaddata <fichier>.
Usage : python manage.py sauvegarder_donnees [--dossier sauvegardes]"""
import gzip
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Exporte la base de données dans un fichier JSON compressé (sauvegardes/uic-AAAAMMJJ-HHMM.json.gz)."

    def add_arguments(self, parser):
        parser.add_argument('--dossier', default='sauvegardes')

    def handle(self, *args, **opts):
        dossier = Path(opts['dossier'])
        dossier.mkdir(parents=True, exist_ok=True)
        cible = dossier / f"uic-{datetime.now():%Y%m%d-%H%M}.json.gz"
        tmp = cible.with_suffix('')  # .json
        with open(tmp, 'w', encoding='utf-8') as f:
            call_command('dumpdata', natural_foreign=True, natural_primary=True, indent=1,
                         exclude=['contenttypes', 'auth.permission', 'admin.logentry', 'sessions'], stdout=f)
        with open(tmp, 'rb') as src, gzip.open(cible, 'wb') as dst:
            dst.write(src.read())
        tmp.unlink()
        self.stdout.write(self.style.SUCCESS(f"Sauvegarde créée : {cible} ({cible.stat().st_size // 1024} Ko)"))
        self.stdout.write("Les photos ajoutées depuis l'administration (dossier media/) ne sont PAS dans ce fichier : copiez aussi ce dossier.")
