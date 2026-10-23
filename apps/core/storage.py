from urllib.parse import urljoin

from django.conf import settings
from whitenoise.storage import CompressedManifestStaticFilesStorage


class TolerantManifestStorage(CompressedManifestStaticFilesStorage):
    """Comme WhiteNoise (noms de fichiers avec empreinte, compression), mais un fichier statique ABSENT ne fait plus
    planter toute la page en erreur 500 : l'image est simplement introuvable (404) et un avertissement est journalisé."""

    def url(self, name, force=False):
        try:
            return super().url(name, force)
        except ValueError:
            import logging
            logging.getLogger(__name__).warning("Fichier statique introuvable : %s", name)
            return urljoin(settings.STATIC_URL, name)
