from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import Http404


def etudiant_requis(view):
    """Connexion obligatoire + profil étudiant ; le profil est passé à la vue.
    Toutes les requêtes de données se font ensuite filtrées sur CE profil."""
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        profil = getattr(request.user, 'profil_etudiant', None)
        if profil is None:
            raise Http404
        return view(request, profil, *args, **kwargs)
    return wrapper
