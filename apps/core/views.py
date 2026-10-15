from django.shortcuts import render
from apps.actualites.models import Article
from apps.admissions.forms import DemandeAdmissionForm
from apps.filieres.models import Filiere
from .models import FAQ, Chiffre, JalonHistoire, Temoignage, Valeur


def home(request):
    articles = list(Article.objects.filter(publie=True).select_related('categorie')[:3])
    return render(request, 'core/home.html', {
        'filieres': Filiere.objects.filter(actif=True),
        'stats_barre': Chiffre.objects.filter(emplacement=Chiffre.BARRE),
        'stats_section': Chiffre.objects.filter(emplacement=Chiffre.SECTION),
        'valeurs': Valeur.objects.filter(zone=Valeur.ACCUEIL),
        'avantages': Valeur.objects.filter(zone=Valeur.POURQUOI),
        'temoignages': Temoignage.objects.filter(actif=True),
        'article_une': articles[0] if articles else None,
        'articles_autres': articles[1:],
        'form': DemandeAdmissionForm(),
    })


def apropos(request):
    return render(request, 'core/apropos.html', {
        'jalons': JalonHistoire.objects.all(),
        'valeurs': Valeur.objects.filter(zone=Valeur.APROPOS),
    })


def faq(request):
    return render(request, 'core/faq.html', {'faqs': FAQ.objects.filter(actif=True)})
