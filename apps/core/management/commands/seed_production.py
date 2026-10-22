"""Initialisation du site RÉEL : structure et informations vérifiables uniquement.

Charge : les 19 formations réelles de l'UIC (source : uic-ci.com), leurs écoles et niveaux.
Ne charge PAS : actualités, chiffres clés, FAQ, valeurs, historique, citation du président.
Ces contenus de démonstration ne sont pas validés : l'UIC les saisit dans l'administration.
Idempotent : ne réécrit jamais ce que l'UIC a modifié dans l'administration, sauf les formations
absentes de la base (une formation existante n'est pas écrasée).

Usage : python manage.py seed_production
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.core.management.commands.seed_uic import charger_formations
from apps.core.models import InfoEtablissement
from apps.filieres.models import Filiere

TEXTE_ACCUEIL = ("L'Université Internationale de Cocody propose des classes préparatoires, des BTS, des licences "
                 "et des masters à Abidjan, ainsi que des formations continues.")


class Command(BaseCommand):
    help = "Initialise le site réel avec les seules données vérifiables (formations réelles)."

    def handle(self, *args, **opts):
        info = InfoEtablissement.get()
        if not info.hero_description:
            info.hero_description = TEXTE_ACCUEIL
        if not info.texte_footer:
            info.texte_footer = "Université Internationale de Cocody — Abidjan, Côte d'Ivoire."
        info.save()
        if Filiere.objects.exists():
            self.stdout.write("Formations déjà présentes : conservées telles quelles (modifiables dans l'administration).")
            return
        d = json.loads((Path(__file__).resolve().parents[2] / 'data' / 'maquette.json').read_text(encoding='utf-8'))
        charger_formations(d)
        self.stdout.write(self.style.SUCCESS(f"{Filiere.objects.filter(actif=True).count()} formations publiées."))
