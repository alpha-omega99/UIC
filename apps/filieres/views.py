from django.shortcuts import get_object_or_404, render
from .models import Filiere


def liste(request):
    return render(request, 'filieres/liste.html', {'filieres': Filiere.objects.filter(actif=True)})


def detail(request, slug):
    f = get_object_or_404(Filiere.objects.prefetch_related('modules'), slug=slug, actif=True)
    semestres = {}
    for m in f.modules.all():
        semestres.setdefault(m.semestre, []).append(m.intitule)
    return render(request, 'filieres/detail.html', {'filiere': f, 'semestres': sorted(semestres.items())})
