from .models import InfoEtablissement
from apps.filieres.models import Filiere


def site_context(request):
    return {
        'site': InfoEtablissement.get(),
        'filieres_footer': Filiere.objects.filter(actif=True).only('nom', 'slug')[:8],
    }
