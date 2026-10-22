"""Publie l'actualité « Cérémonie de remise des diplômes » avec l'album photos correspondant.
Ne s'exécute qu'une seule fois (marqueur en base) : si l'article est ensuite modifié ou supprimé dans l'administration,
il n'est jamais recréé ni écrasé. Usage : python manage.py ajouter_ceremonie_diplomes [--forcer]"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.actualites.models import Article, Categorie
from apps.core.models import CorrectionAppliquee
from apps.galerie.models import Album

MARQUEUR = 'actualite-ceremonie-diplomes-v1'


class Command(BaseCommand):
    help = "Ajoute l'actualité de la cérémonie de remise des diplômes (une seule fois)."

    def add_arguments(self, parser):
        parser.add_argument('--forcer', action='store_true', help="Recrée l'actualité si le marqueur existe déjà")

    def handle(self, *args, **opts):
        if CorrectionAppliquee.objects.filter(empreinte=MARQUEUR).exists() and not opts['forcer']:
            self.stdout.write("Actualité de la cérémonie déjà ajoutée : ignorée.")
            return
        album = Album.objects.filter(slug='ceremonie-diplomes').first()
        if not album or not album.photos.exists():
            self.stdout.write(self.style.WARNING("Album « ceremonie-diplomes » absent : lancez d'abord seed_images."))
            return
        cat, _ = Categorie.objects.get_or_create(nom='Événement')
        article, cree = Article.objects.get_or_create(slug='ceremonie-remise-des-diplomes', defaults=dict(
            categorie=cat, titre="Cérémonie de remise des diplômes",
            chapeau="Retour en images sur la cérémonie de remise des diplômes de l'UIC.",
            contenu=("Les diplômés de l'UIC ont reçu leurs diplômes lors d'une cérémonie organisée sur le campus de Cocody, "
                     "en compagnie de leurs proches, de leurs enseignants et de la direction de l'université.\n\n"
                     "Toges, écharpes et sourires : retrouvez ci-dessous les moments forts de la journée."),
            image_statique=album.photos.first().image_statique, album=album, temps_lecture=1, publie=True,
            date_publication=timezone.now()))
        CorrectionAppliquee.objects.get_or_create(empreinte=MARQUEUR, defaults={'resume': "Actualité cérémonie de remise des diplômes"})
        self.stdout.write(self.style.SUCCESS("Actualité ajoutée." if cree else "Actualité déjà présente (marqueur posé)."))
