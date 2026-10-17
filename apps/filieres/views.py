from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Filiere, NiveauFormation, Pole


def niveaux_utilises(queryset_filieres=None):
    """Niveaux ayant au moins une filière publiée (les filtres vides n'apparaissent pas)."""
    return (NiveauFormation.objects
            .annotate(nb=Count('filieres', filter=Q(filieres__actif=True), distinct=True))
            .filter(nb__gt=0))


def liste(request):
    filieres = list(Filiere.objects.filter(actif=True).select_related('pole').prefetch_related('niveaux'))
    # Regroupement par école / département (les formations sans école vont à la fin)
    groupes, index = [], {}
    for f in filieres:
        cle = f.pole_id
        if cle not in index:
            index[cle] = {'pole': f.pole, 'filieres': []}
            groupes.append(index[cle])
        index[cle]['filieres'].append(f)
    groupes.sort(key=lambda g: (g['pole'] is None, g['pole'].ordre if g['pole'] else 0, g['pole'].nom if g['pole'] else ''))
    poles = [g['pole'] for g in groupes if g['pole']]
    for g in groupes:
        g['nb'] = len(g['filieres'])
    return render(request, 'filieres/liste.html', {
        'groupes': groupes, 'poles': poles, 'niveaux': niveaux_utilises(), 'total': len(filieres),
        'a_des_poles': bool(poles)})


def detail(request, slug):
    f = get_object_or_404(Filiere.objects.prefetch_related('modules', 'niveaux'), slug=slug, actif=True)
    semestres = {}
    for m in f.modules.all():
        semestres.setdefault(m.semestre, []).append(m.intitule)
    niveaux_ids = [n.pk for n in f.niveaux.all()]
    voisines = (Filiere.objects.filter(actif=True).exclude(pk=f.pk).prefetch_related('niveaux')
                .annotate(commun=Count('niveaux', filter=Q(niveaux__in=niveaux_ids), distinct=True))
                .order_by('-commun', 'ordre', 'nom')[:3])
    return render(request, 'filieres/detail.html', {'filiere': f, 'semestres': sorted(semestres.items()), 'voisines': voisines})
