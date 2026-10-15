import os
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.contrib.auth import logout
from django.shortcuts import redirect
from django_ratelimit.decorators import ratelimit
from apps.core.utils import client_ip
from .decorators import etudiant_requis
from .forms import EtudiantAuthForm
from .models import CarteAdmission, Certificat, Resultat


# ── Authentification (anti brute-force : par IP ET par identifiant) ──────────
@method_decorator(never_cache, name='dispatch')
@method_decorator(ratelimit(key=client_ip, rate='15/15m', method='POST', block=True), name='dispatch')
@method_decorator(ratelimit(key='post:username', rate='6/15m', method='POST', block=True), name='dispatch')
class Connexion(auth_views.LoginView):
    template_name = 'portail/connexion.html'
    authentication_form = EtudiantAuthForm
    redirect_authenticated_user = True     # `next` est validé par Django (pas d'open redirect)


@require_POST
def deconnexion(request):
    logout(request)
    messages.success(request, 'Vous êtes déconnecté.')
    return redirect('core:home')


class ChangerMotDePasse(auth_views.PasswordChangeView):
    template_name = 'portail/mot_de_passe.html'
    success_url = reverse_lazy('portail:tableau_de_bord')

    def form_valid(self, form):
        messages.success(self.request, 'Mot de passe modifié.')
        return super().form_valid(form)


@method_decorator(ratelimit(key=client_ip, rate='5/h', method='POST', block=True), name='dispatch')
class ReinitMotDePasse(auth_views.PasswordResetView):
    template_name = 'registration/reset_form.html'
    email_template_name = 'registration/reset_email.txt'
    subject_template_name = 'registration/reset_subject.txt'
    success_url = reverse_lazy('portail:reset_envoye')


# ── Espace étudiant ──────────────────────────────────────────────────────────
@never_cache
@etudiant_requis
def tableau_de_bord(request, profil):
    return render(request, 'portail/tableau_de_bord.html', {
        'profil': profil,
        'resultats': profil.resultats.filter(publie=True)[:5],
        'nb_cartes': profil.cartes.filter(publie=True).count(),
        'nb_certificats': profil.certificats.filter(publie=True).count(),
    })


@never_cache
@etudiant_requis
def resultats(request, profil):
    qs = profil.resultats.filter(publie=True)
    annees = list(qs.order_by('-annee_academique').values_list('annee_academique', flat=True).distinct())
    annee = request.GET.get('annee')
    if annee in annees:            # n'accepte qu'une valeur existante
        qs = qs.filter(annee_academique=annee)
    else:
        annee = ''
    liste = list(qs)
    moyenne = round(sum(r.sur_20 for r in liste) / len(liste), 2) if liste else None
    return render(request, 'portail/resultats.html', {'profil': profil, 'resultats': liste, 'annees': annees,
                                                      'annee': annee, 'moyenne': moyenne})


@never_cache
@etudiant_requis
def cartes(request, profil):
    return render(request, 'portail/cartes.html', {'profil': profil, 'cartes': profil.cartes.filter(publie=True)})


@never_cache
@etudiant_requis
def certificats(request, profil):
    return render(request, 'portail/certificats.html', {'profil': profil, 'certificats': profil.certificats.filter(publie=True)})


@etudiant_requis
def telecharger(request, profil, type_doc, pk):
    """Seul le propriétaire connecté peut télécharger son document publié."""
    if type_doc == 'carte':
        doc = get_object_or_404(CarteAdmission, pk=pk, etudiant=profil, publie=True)
    elif type_doc == 'certificat':
        doc = get_object_or_404(Certificat, pk=pk, etudiant=profil, publie=True)
    else:
        raise Http404
    try:
        handle = doc.fichier.open('rb')
    except (FileNotFoundError, ValueError):
        raise Http404
    resp = FileResponse(handle, as_attachment=True, filename=os.path.basename(doc.fichier.name))
    resp['X-Content-Type-Options'] = 'nosniff'
    resp['Cache-Control'] = 'private, no-store'
    return resp
