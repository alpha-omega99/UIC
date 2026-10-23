from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from apps.galerie.models import Album
from .models import Article


def liste(request):
    qs = Article.objects.filter(publie=True).select_related('categorie', 'album')
    page = Paginator(qs, 9).get_page(request.GET.get('page'))
    objets = list(page.object_list)
    # Chaque actualité liée à un album devient un « événement » avec sa mosaïque de photos ; les autres vont aux archives.
    evenements = [{'article': a, 'moments': list(a.album.photos.all()[:10])} for a in objets if a.album_id][:3]
    ids = {e['article'].pk for e in evenements}
    archives = [a for a in objets if a.pk not in ids]
    return render(request, 'actualites/liste.html', {'page': page, 'evenements': evenements, 'archives': archives,
                  'albums': Album.objects.filter(actif=True).prefetch_related('photos')})


def detail(request, slug):
    a = get_object_or_404(Article.objects.select_related('categorie'), slug=slug, publie=True)
    autres = Article.objects.filter(publie=True).exclude(pk=a.pk).select_related('categorie')[:2]
    moments = list(a.album.photos.all()[:12]) if a.album_id else []
    return render(request, 'actualites/detail.html', {'article': a, 'autres': autres, 'moments': moments})
