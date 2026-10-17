from django.shortcuts import render
from apps.actualites.models import Article
from apps.admissions.forms import DemandeAdmissionForm
from apps.filieres.models import Filiere
from apps.galerie.models import Album, Photo
from .models import FAQ, Chiffre, JalonHistoire, Partenaire, Valeur


def niveaux_utilises_accueil():
    from django.db.models import Count, Q
    from apps.filieres.models import NiveauFormation
    return (NiveauFormation.objects
            .annotate(nb=Count('filieres', filter=Q(filieres__actif=True, filieres__en_avant=True), distinct=True))
            .filter(nb__gt=0))


def photos_accueil(max_total=12, par_album=3):
    """Quelques photos de chaque album actif, pour la section « Vie du campus » de l'accueil."""
    photos = []
    for album in Album.objects.filter(actif=True).prefetch_related('photos'):
        photos.extend(list(album.photos.all()[:par_album]))
    return photos[:max_total]


def home(request):
    articles = list(Article.objects.filter(publie=True).select_related('categorie')[:3])
    return render(request, 'core/home.html', {
        'filieres': Filiere.objects.filter(actif=True, en_avant=True).prefetch_related('niveaux')[:6],
        'niveaux': niveaux_utilises_accueil(),
        'total_filieres': Filiere.objects.filter(actif=True).count(),
        'stats_barre': Chiffre.objects.filter(emplacement=Chiffre.BARRE),
        'stats_section': Chiffre.objects.filter(emplacement=Chiffre.SECTION),
        'valeurs': Valeur.objects.filter(zone=Valeur.ACCUEIL),
        'avantages': Valeur.objects.filter(zone=Valeur.POURQUOI),
        'partenaires': Partenaire.objects.filter(actif=True),
        'article_une': articles[0] if articles else None,
        'articles_autres': articles[1:],
        'photos_campus': photos_accueil(),
        'form': DemandeAdmissionForm(),
    })


def apropos(request):
    return render(request, 'core/apropos.html', {
        'jalons': JalonHistoire.objects.all(),
        'valeurs': Valeur.objects.filter(zone=Valeur.APROPOS),
    })


def faq(request):
    return render(request, 'core/faq.html', {'faqs': FAQ.objects.filter(actif=True)})


LEGAL_MAJ = "17 octobre 2026"


def mentions_legales(request):
    return render(request, 'legal/mentions.html', {'maj': LEGAL_MAJ})


def confidentialite(request):
    return render(request, 'legal/confidentialite.html', {'maj': LEGAL_MAJ})


def conditions(request):
    return render(request, 'legal/conditions.html', {'maj': LEGAL_MAJ})
