"""Notification par e-mail des formulaires (admission, contact).

La soumission est TOUJOURS enregistrée en base (visible dans l'admin) ; l'e-mail est un plus.
Si l'envoi échoue, on journalise l'erreur mais le visiteur ne voit aucune erreur.

Deux modes d'envoi :
  1. API HTTPS Brevo si BREVO_API_KEY est défini (fonctionne aussi sur l'hébergement gratuit de Render,
     qui bloque le SMTP) ;
  2. sinon SMTP classique (Gmail, etc.) via les variables EMAIL_*.
"""
import json
import logging
import urllib.request

from django.conf import settings
from django.core.mail import EmailMessage

log = logging.getLogger(__name__)


def propre(s):
    return ' '.join(str(s).split())          # anti-injection d'en-têtes


def destinataires():
    """NOTIFY_EMAIL accepte plusieurs adresses séparées par des virgules."""
    return [a.strip() for a in str(settings.NOTIFY_EMAIL).replace(';', ',').split(',') if a.strip()]


def _expediteur():
    nom, adr = settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL
    if '<' in nom:
        nom, adr = nom.split('<', 1)
        adr = adr.rstrip('> ')
    return nom.strip() or 'UIC', adr.strip()


def _envoyer_brevo(sujet, corps, reply_to):
    nom, adr = _expediteur()
    data = {'sender': {'name': nom, 'email': adr}, 'to': [{'email': a} for a in destinataires()],
            'subject': sujet, 'textContent': corps}
    if reply_to:
        data['replyTo'] = {'email': reply_to}
    req = urllib.request.Request(
        'https://api.brevo.com/v3/smtp/email', data=json.dumps(data).encode(), method='POST',
        headers={'api-key': settings.BREVO_API_KEY, 'content-type': 'application/json', 'accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as r:      # noqa: S310 (URL fixe https)
        return r.status < 300


def notifier(sujet, corps, reply_to=None):
    """Envoie la notification ; renvoie True si OK, False sinon (jamais d'exception)."""
    sujet, to = propre(sujet), destinataires()
    if not to:
        log.warning('NOTIFY_EMAIL vide : notification non envoyée (%s)', sujet)
        return False
    try:
        if getattr(settings, 'BREVO_API_KEY', ''):
            return _envoyer_brevo(sujet, corps, reply_to)
        EmailMessage(subject=sujet, body=corps, from_email=settings.DEFAULT_FROM_EMAIL, to=to,
                     reply_to=[reply_to] if reply_to else None).send(fail_silently=False)
        return True
    except Exception:                                        # réseau, SMTP bloqué, mauvais mot de passe…
        log.exception("Échec d'envoi de la notification e-mail : %s", sujet)
        return False
