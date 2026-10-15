from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django_ratelimit.decorators import ratelimit
from apps.core.utils import client_ip
from .forms import DemandeAdmissionForm, SuiviForm
from .models import DemandeAdmission


def _clean(s):
    return ' '.join(str(s).split())          # supprime les retours à la ligne (anti-injection d'en-têtes)


@ratelimit(key=client_ip, rate='6/h', method='POST', block=True)
def formulaire(request):
    if request.method == 'POST':
        form = DemandeAdmissionForm(request.POST)
        if form.is_valid():
            d = form.save()
            send_mail(
                subject=_clean(f'[UIC] Nouvelle candidature {d.numero_dossier} — {d.prenom} {d.nom}'),
                message=(f"Dossier : {d.numero_dossier}\nCandidat : {d.prenom} {d.nom}\nEmail : {d.email}\n"
                         f"Téléphone : {d.telephone or '—'}\nFilière : {d.filiere}\nNiveau : {d.get_niveau_entree_display()}\n"),
                from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[settings.NOTIFY_EMAIL], fail_silently=True)
            request.session['dernier_dossier'] = d.numero_dossier
            return redirect('admissions:merci')
        messages.error(request, 'Veuillez corriger les champs signalés.')
    else:
        form = DemandeAdmissionForm()
    return render(request, 'admissions/formulaire.html', {'form': form})


def merci(request):
    numero = request.session.get('dernier_dossier')
    if not numero:
        return redirect('admissions:formulaire')
    return render(request, 'admissions/merci.html', {'numero': numero})


@ratelimit(key=client_ip, rate='10/15m', method='POST', block=True)
def suivi(request):
    dossier, cherche = None, False
    form = SuiviForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cherche = True
        dossier = DemandeAdmission.objects.filter(
            email=form.cleaned_data['email'], numero_dossier=form.cleaned_data['numero']).select_related('filiere').first()
    return render(request, 'admissions/suivi.html', {'form': form, 'dossier': dossier, 'cherche': cherche})
