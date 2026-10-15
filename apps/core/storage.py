"""Stockage PRIVÉ (hors MEDIA_ROOT) : aucun document étudiant n'a d'URL publique."""
from django.conf import settings
from django.core.files.storage import FileSystemStorage


def private_storage():
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)
