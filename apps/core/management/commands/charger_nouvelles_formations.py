"""Charge les 10 licences + 10 masters professionnels (fiches fournies par la direction).

Par défaut, une formation déjà présente (même slug) n'est PAS écrasée : les modifications faites
dans l'administration sont conservées. Utiliser --forcer pour tout remettre à l'état du fichier."""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.filieres.models import Filiere, NiveauFormation, Pole

DESC_POLES = {
    'Pôle Gestion & Finance': "Gérer, comptabiliser, auditer et piloter les ressources humaines des entreprises.",
    'Pôle Commerce & Communication': "Vendre, communiquer, transporter : les métiers du commerce et du digital.",
    'Pôle Industriel': "Qualité, sécurité, production et maintenance pour l'industrie.",
}
CHAMPS = ('nom', 'icone', 'resume', 'objectif', 'public_cible', 'organisation', 'programme', 'competences', 'debouches',
          'repere_salaire', 'atouts', 'admission', 'frais', 'accroche', 'duree', 'mode', 'niveau_requis',
          'image_statique', 'ordre')


class Command(BaseCommand):
    help = "Charge les nouvelles licences et masters professionnels (rentrée 2026-2027)."

    def add_arguments(self, parser):
        parser.add_argument('--forcer', action='store_true', help="Écrase aussi les formations déjà présentes")

    def handle(self, *args, **opts):
        data = json.loads((Path(__file__).resolve().parents[2] / 'data' / 'nouvelles_formations.json').read_text(encoding='utf-8'))
        base = Pole.objects.count()
        for nom in ('Licence professionnelle', 'Master professionnel'):
            NiveauFormation.objects.get_or_create(nom=nom, defaults={'ordre': 10})
        crees = 0
        for f in data:
            pole, nouveau_pole = Pole.objects.get_or_create(nom=f['pole'], defaults={'description': DESC_POLES.get(f['pole'], '')})
            if nouveau_pole:
                Pole.objects.filter(pk=pole.pk).update(ordre=base + list(DESC_POLES).index(f['pole']))
            existe = Filiere.objects.filter(slug=f['slug']).first()
            if existe and not opts['forcer']:
                continue
            vals = {k: f[k] for k in CHAMPS}
            obj, cree = Filiere.objects.update_or_create(slug=f['slug'], defaults=dict(
                **vals, pole=pole, nouveau=True, en_avant=False, actif=True, langue='Français'))
            obj.niveaux.set(NiveauFormation.objects.filter(nom__in=f['niveaux']))
            crees += cree
        for f in data:
            if f['licence_associee']:
                Filiere.objects.filter(slug=f['slug'], licence_associee__isnull=True).update(
                    licence_associee=Filiere.objects.filter(slug=f['licence_associee']).first())
        self.stdout.write(self.style.SUCCESS(f"{crees} nouvelle(s) formation(s) ajoutée(s) ; "
                                             f"{Filiere.objects.filter(nouveau=True).count()} en tout marquées « nouveau »."))