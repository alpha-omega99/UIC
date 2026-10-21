from django.shortcuts import get_object_or_404, redirect, render
from .models import Album


def liste(request):
    # La galerie est désormais un onglet de la page « Actualités & galerie »
    return redirect('/actualites/#galerie')


def detail(request, slug):
    a = get_object_or_404(Album, slug=slug, actif=True)
    return render(request, 'galerie/detail.html', {'album': a, 'photos': a.photos.all()})
