"""Affiche le contenu modifiable (chiffres, histoire, valeurs, FAQ…) avec le « repere » exact à copier dans corrections.csv.
Usage : python manage.py lister_contenu"""
from django.core.management.base import BaseCommand

from apps.actualites.models import Article
from apps.core.models import FAQ, Chiffre, InfoEtablissement, JalonHistoire, Valeur


class Command(BaseCommand):
    help = "Liste le contenu existant et les repères à utiliser dans le fichier de corrections."

    def handle(self, *args, **opts):
        w = self.stdout.write
        w("\n== CHIFFRES  (cible: chiffre ; repere: le libellé ; champs: valeur, suffixe, libelle) ==")
        for c in Chiffre.objects.all():
            w(f"  [{c.emplacement}] {c.valeur}{c.suffixe}  |  repere = {c.libelle}")
        w("\n== HISTOIRE  (cible: jalon ; repere: l'année ; champs: annee, titre, texte) ==")
        for j in JalonHistoire.objects.all():
            w(f"  repere = {j.annee}  |  {j.titre}")
        w("\n== VALEURS  (cible: valeur ; repere: le titre ; champs: titre, texte, icone) ==")
        for v in Valeur.objects.all():
            w(f"  [{v.zone}] repere = {v.titre}")
        w("\n== FAQ  (cible: faq ; repere: la question ; champs: question, reponse) ==")
        for f in FAQ.objects.all():
            w(f"  repere = {f.question}")
        w("\n== ACTUALITÉS  (cible: article ; repere: le titre ; champs: titre, chapeau, contenu, publie) ==")
        for a in Article.objects.all():
            w(f"  repere = {a.titre}")
        w("\n== INFORMATIONS DE L'ÉTABLISSEMENT  (cible: info ; repere: laisser vide ; champ: nom du champ) ==")
        w("  champs : " + ', '.join(f.name for f in InfoEtablissement._meta.fields if f.name != 'id'))
