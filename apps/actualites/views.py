from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from apps.galerie.models import Album
from .models import Article


def liste(request):
    qs = Article.objects.filter(publie=True).select_related('categorie', 'album')
    page = Paginator(qs, 9).get_page(request.GET.get('page'))
    objets = list(page.object_list)
    # Page 1 : le dernier article est mis en avant (avec ses « Moments forts »), les autres vont dans les archives
    vedette = objets[0] if page.number == 1 and objets else None
    archives = objets[1:] if vedette else objets
    moments = list(vedette.album.photos.all()[:10]) if vedette and vedette.album_id else []
    return render(request, 'actualites/liste.html', {
        'page': page, 'vedette': vedette, 'archives': archives, 'moments': moments,
        'albums': Album.objects.filter(actif=True).prefetch_related('photos')})


def detail(request, slug):
    a = get_object_or_404(Article.objects.select_related('categorie'), slug=slug, publie=True)
    autres = Article.objects.filter(publie=True).exclude(pk=a.pk).select_related('categorie')[:2]
    moments = list(a.album.photos.all()[:12]) if a.album_id else []
    return render(request, 'actualites/detail.html', {'article': a, 'autres': autres, 'moments': moments})
