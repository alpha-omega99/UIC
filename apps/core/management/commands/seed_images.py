"""Affecte les images du dossier static/img aux filières, actualités, galerie et partenaires.
Idempotent et sans écrasement : ne touche jamais à une image déjà choisie dans l'administration.
Usage : python manage.py seed_images"""
import json
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.actualites.models import Article
from apps.core.models import Partenaire
from apps.filieres.models import Filiere
from apps.galerie.models import Album, Photo


class Command(BaseCommand):
    help = "Associe les images du site (static/img) au contenu"

    def handle(self, *args, **opts):
        d = json.loads((Path(__file__).resolve().parents[2] / 'data' / 'images.json').read_text(encoding='utf-8'))
        manquants = []

        def verifier(chemin):
            ok = any((Path(root) / chemin).exists() for root in
                     [Path(settings.BASE_DIR) / 'static'] + [Path(p) for p in settings.STATICFILES_DIRS])
            if not ok:
                manquants.append(chemin)
            return ok

        n = 0
        for slug, chemin in d['filieres'].items():
            if verifier(chemin):
                n += Filiere.objects.filter(slug=slug, image='', image_statique='').update(image_statique=chemin, image_url='')
        for slug, chemin in d['articles'].items():
            if verifier(chemin):
                n += Article.objects.filter(slug=slug, image='', image_statique='').update(image_statique=chemin, image_url='')

        for a in d['albums']:
            album, cree = Album.objects.get_or_create(slug=a['slug'], defaults=dict(
                titre=a['titre'], description=a['description'], date=date.fromisoformat(a['date'])))
            if not album.photos.exists():
                for i, (chemin, legende) in enumerate(a['photos']):
                    if verifier(chemin):
                        Photo.objects.create(album=album, image_statique=chemin, legende=legende, ordre=i)

        for p in d['partenaires']:
            if verifier(p['logo']):
                Partenaire.objects.get_or_create(nom=p['nom'], defaults=dict(
                    pays=p['pays'], logo_statique=p['logo'], site_web=p['site_web'], ordre=p['ordre']))

        for m in manquants:
            self.stderr.write(f"Image introuvable : static/{m}")
        self.stdout.write(self.style.SUCCESS(f"Images associées ({n} fiches mises à jour, {Album.objects.count()} albums, {Partenaire.objects.count()} partenaires)."))
