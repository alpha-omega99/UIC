import re
from django.templatetags.static import static
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

validate_image = FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])
validate_document = FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])


def client_ip(group, request):
    """IP réelle derrière le proxy Render (dernière entrée de X-Forwarded-For, non falsifiable)."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return xff.split(',')[-1].strip() if xff else request.META.get('REMOTE_ADDR', '')


PHONE_RE = re.compile(r'^\+?[\d\s().-]{8,20}$')


def validate_phone(value):
    if value and not PHONE_RE.match(value):
        raise ValidationError("Numéro de téléphone invalide.")


def image_source(upload, statique='', url=''):
    """URL d'une image : fichier téléversé > image du dossier static > URL externe."""
    if upload:
        return upload.url
    if statique:
        try:
            return static(statique)
        except ValueError:      # fichier absent du dossier static (ex : oublié dans Git) : on n'affiche pas d'image plutôt que de planter la page
            import logging
            logging.getLogger(__name__).warning("Image statique introuvable : %s", statique)
            return url or ''
    return url or ''
