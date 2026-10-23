"""Supprime de la base les tables de l'ancien « espace étudiant » (app portail : profils, résultats, cartes, certificats).
Sans danger et répétable : s'il n'y a plus rien à supprimer, la commande ne fait rien. Peut être lancée avant ou après la mise à jour du code.
Option --comptes : supprime aussi les comptes de connexion des étudiants (utilisateurs non-staff). Les comptes administrateur ne sont JAMAIS touchés.
Usage : python manage.py supprimer_espace_etudiant [--comptes]"""
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Supprime les tables de l'ancien espace étudiant (portail)."

    def add_arguments(self, parser):
        parser.add_argument('--comptes', action='store_true', help="Supprime aussi les comptes étudiants (non-staff)")

    def handle(self, *args, **opts):
        tables = [t for t in connection.introspection.table_names() if t.startswith('portail_')]
        with transaction.atomic():
            for t in tables:
                suffixe = ' CASCADE' if connection.vendor == 'postgresql' else ''
                connection.cursor().execute(f'DROP TABLE IF EXISTS {connection.ops.quote_name(t)}{suffixe}')
            if 'django_migrations' in connection.introspection.table_names():
                connection.cursor().execute("DELETE FROM django_migrations WHERE app = 'portail'")
            ContentType.objects.filter(app_label='portail').delete()
            nb = 0
            if opts['comptes']:
                nb, _ = get_user_model().objects.filter(is_staff=False, is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS(
            f"{len(tables)} table(s) supprimée(s)." + (f" {nb} objet(s) de comptes étudiants supprimé(s)." if opts['comptes'] else "")))
