from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from apps.galerie.models import Album
from .models import Article


def liste(request):
    qs = Article.objects.filter(publie=True).select_related('categorie')
    page = Paginator(qs, 9).get_page(request.GET.get('page'))
    return render(request, 'actualites/liste.html', {'page': page, 'albums': Album.objects.filter(actif=True).prefetch_related('photos')})


def detail(request, slug):
    a = get_object_or_404(Article.objects.select_related('categorie'), slug=slug, publie=True)
    autres = Article.objects.filter(publie=True).exclude(pk=a.pk).select_related('categorie')[:2]
    return render(request, 'actualites/detail.html', {'article': a, 'autres': autres})
