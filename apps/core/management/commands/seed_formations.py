import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.core.management.commands.seed_uic import charger_formations
from apps.filieres.models import Filiere


class Command(BaseCommand):
    help = "Charge uniquement les formations réelles de l'UIC (ne touche ni aux actualités, ni aux chiffres, ni à la FAQ)."

    def handle(self, *args, **opts):
        d = json.loads((Path(__file__).resolve().parents[2] / 'data' / 'maquette.json').read_text(encoding='utf-8'))
        charger_formations(d)
        self.stdout.write(self.style.SUCCESS(f"{Filiere.objects.filter(actif=True).count()} formations publiées."))
