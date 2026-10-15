import re
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
