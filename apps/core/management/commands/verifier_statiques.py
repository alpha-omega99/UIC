"""Vérifie que tous les fichiers statiques utilisés par le site existent (images, logos, vidéo, CSS, JS).
Lit les {% static '...' %} des gabarits et les chemins « img/... » des fichiers de données.
Avec --strict, la commande échoue et liste les fichiers manquants (utile avant un déploiement : Render garde alors l'ancienne version en ligne).
Usage : python manage.py verifier_statiques [--strict]"""
import re
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand, CommandError

STATIC_RE = re.compile(r"""\{%\s*static\s+['"]([^'"]+)['"]\s*%\}""")
DATA_RE = re.compile(r'"((?:img|video|css|js)/[^"\s]+\.(?:webp|jpg|jpeg|png|svg|gif|mp4|css|js))"')


class Command(BaseCommand):
    help = "Vérifie la présence des fichiers statiques référencés."

    def add_arguments(self, parser):
        parser.add_argument('--strict', action='store_true', help="Échoue si un fichier manque")

    def handle(self, *args, **opts):
        base = Path(settings.BASE_DIR)
        refs = {}
        for f in (base / 'templates').rglob('*.html'):
            for m in STATIC_RE.finditer(f.read_text(encoding='utf-8')):
                refs.setdefault(m.group(1), str(f.relative_to(base)))
        for f in (base / 'apps').rglob('data/*.json'):
            for m in DATA_RE.finditer(f.read_text(encoding='utf-8')):
                refs.setdefault(m.group(1), str(f.relative_to(base)))
        manquants = sorted((p, src) for p, src in refs.items() if '{{' not in p and not finders.find(p))
        for p, src in manquants:
            self.stdout.write(self.style.ERROR(f"MANQUANT : static/{p}   (utilisé dans {src})"))
        self.stdout.write(f"{len(refs)} fichiers statiques référencés, {len(manquants)} manquant(s).")
        if manquants and opts['strict']:
            raise CommandError("Fichiers statiques manquants : ajoutez-les à Git (git add static) puis poussez.")
