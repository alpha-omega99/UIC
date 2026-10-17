"""Charge dans la base le contenu EXACT de la maquette d'origine (idempotent).
Usage : python manage.py seed_uic [--demo-etudiant]"""
import json
import secrets
from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.actualites.models import Article, Categorie
from apps.core.models import FAQ, Chiffre, InfoEtablissement, JalonHistoire, Valeur
from apps.filieres.models import Filiere, Module, NiveauFormation, Pole
from apps.portail.models import ProfilEtudiant, Resultat

MOIS = {m: i for i, m in enumerate(['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
                                    'septembre', 'octobre', 'novembre', 'décembre'], 1)}


def parse_date(s):
    j, m, a = s.lower().split()
    return timezone.make_aware(datetime(int(a), MOIS[m], int(j), 9, 0))



def charger_formations(d):
    """Charge (ou met à jour) les formations réelles de l'UIC. Utilisable seule : python manage.py seed_formations"""
    # Formations réelles (source : uic-ci.com, page « Filières », et affiches de l'établissement)
    for i, nom in enumerate(['Classe préparatoire', 'BTS', 'Licence', 'Master', 'Licence professionnelle',
                             'Master professionnel', 'Formation continue']):
        NiveauFormation.objects.get_or_create(nom=nom, defaults={'ordre': i})
    for f in d['filieres']:
        pole = None
        if f.get('pole'):
            pole, _ = Pole.objects.get_or_create(nom=f['pole'])
        obj, _ = Filiere.objects.update_or_create(slug=f['slug'], defaults=dict(
            nom=f['nom'], icone=f['icone'], resume=f['resume'], sous_titre=f['sous_titre'], description=f['description'],
            duree=f['duree'], niveau_requis=f['niveau_requis'], mode=f['mode'], langue=f['langue'],
            debouches='\n'.join(f['debouches']), image_statique=f['image_statique'], image_url='',
            ordre=f['ordre'], en_avant=f['en_avant'], pole=pole, actif=True))
        obj.niveaux.set(NiveauFormation.objects.filter(nom__in=f['niveaux']))
    # Anciennes formations de démonstration : supprimées (ou masquées si une candidature y est liée)
    for old in Filiere.objects.filter(slug__in=['management', 'informatique', 'droit', 'finance', 'commerce', 'communication']):
        if old.candidatures.exists():
            old.actif = False
            old.save(update_fields=['actif'])
        else:
            old.delete()
    # Ordre des écoles = ordre d'apparition dans les données
    for i, nom in enumerate(dict.fromkeys(f['pole'] for f in d['filieres'] if f.get('pole'))):
        Pole.objects.filter(nom=nom).update(ordre=i)


class Command(BaseCommand):
    help = "Charge le contenu de la maquette UIC"

    def add_arguments(self, parser):
        parser.add_argument('--demo-etudiant', action='store_true', help="Crée un étudiant de démonstration (DEV uniquement)")

    def handle(self, *args, **opts):
        d = json.loads((Path(__file__).resolve().parents[2] / 'data' / 'maquette.json').read_text(encoding='utf-8'))

        info = InfoEtablissement.get()
        info.hero_description = ("L'UIC existe depuis 2004 à Cocody. Des profs qui ont exercé dans de vraies entreprises, "
                                 "des stages dans de vraies structures, des diplômés qui trouvent du travail — parfois avant même de soutenir.")
        info.texte_footer = ("Depuis 2004, on forme des gens qui travaillent. Pas des diplômés sur papier — "
                             "des professionnels attendus par leurs recruteurs le lundi matin.")
        info.president_citation = d['president']['citation']
        info.president_texte = d['president']['texte']
        info.maps_embed = ("https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3972.4!2d-3.9947!3d5.3587!2m3!1f0!2f0!3f0!3m2!1i1024!2i768"
                           "!4f13.1!3m3!1m2!1s0x0%3A0x0!2zNcKwMjEnMzEuMyJOIDPCsDU5JzQxLjAiVw!5e0!3m2!1sfr!2sci!4v1")
        info.save()

        charger_formations(d)

        for a in d['articles']:
            cat, _ = Categorie.objects.get_or_create(nom=a['categorie'])
            Article.objects.update_or_create(slug=a['slug'], defaults=dict(
                categorie=cat, titre=a['titre'], chapeau=a['chapeau'], contenu=a['contenu'], image_url=a['image_url'],
                temps_lecture=a['temps_lecture'], publie=True, date_publication=parse_date(a['date'])))

        Chiffre.objects.all().delete()
        for i, s in enumerate(d['stats_barre']):
            Chiffre.objects.create(emplacement='barre', ordre=i, **s)
        for i, s in enumerate(d['stats_section']):
            Chiffre.objects.create(emplacement='section', ordre=i, **s)

        Valeur.objects.all().delete()
        for zone, key in (('accueil', 'valeurs_accueil'), ('apropos', 'valeurs_apropos'), ('pourquoi', 'avantages')):
            for i, v in enumerate(d[key]):
                Valeur.objects.create(zone=zone, ordre=i, **v)

        JalonHistoire.objects.all().delete()
        for j in d['jalons']:
            JalonHistoire.objects.create(**j)

        FAQ.objects.all().delete()
        for i, q in enumerate(d['faq']):
            FAQ.objects.create(ordre=i, **q)

        self.stdout.write(self.style.SUCCESS(
            f"Contenu chargé : {Filiere.objects.count()} filières, {Article.objects.count()} actualités, "
            f"{FAQ.objects.count()} FAQ."))

        if opts['demo_etudiant']:
            U = get_user_model()
            pwd = secrets.token_urlsafe(12)
            u, created = U.objects.get_or_create(username='UIC-DEMO-001', defaults=dict(first_name='Awa', last_name='Démo', email='demo@example.com'))
            u.set_password(pwd); u.save()
            p, _ = ProfilEtudiant.objects.get_or_create(user=u, defaults=dict(
                matricule='UIC-DEMO-001', filiere=Filiere.objects.first(), niveau='Licence 2', annee_inscription=2024))
            if not p.resultats.exists():
                for m, n in (('Comptabilité générale', 14.5), ('Droit des affaires', 11), ('Économie générale', 9)):
                    Resultat.objects.create(etudiant=p, matiere=m, note=n, semestre=1, annee_academique='2025-2026', publie=True)
            self.stdout.write(self.style.WARNING(f"Étudiant démo → identifiant : UIC-DEMO-001 | mot de passe : {pwd}  (à supprimer avant la mise en ligne)"))
