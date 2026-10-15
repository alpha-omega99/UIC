from django.shortcuts import get_object_or_404, render
from .models import Album


def liste(request):
    return render(request, 'galerie/liste.html', {'albums': Album.objects.filter(actif=True).prefetch_related('photos')})


def detail(request, slug):
    a = get_object_or_404(Album, slug=slug, actif=True)
    return render(request, 'galerie/detail.html', {'album': a, 'photos': a.photos.all()})
