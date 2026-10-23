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


CYCLES = [
    ('Classes préparatoires', '🎓', ['classe-preparatoire'], "Préparation aux grandes écoles et aux cycles sélectifs.", 'img/campus/salle-de-cours-03.webp'),
    ('BTS', '📘', ['bts'], "Des formations de niveau Bac +2, tournées vers l'emploi.", 'img/campus/travail-en-groupe-01.webp'),
    ('Licences', '🏛️', ['licence', 'licence-professionnelle'], "Licences LMD et licences professionnelles.", 'img/campus/salle-de-cours-01.webp'),
    ('Masters', '🎯', ['master', 'master-professionnel'], "Masters LMD et masters professionnels.", 'img/campus/vie-etudiante-05.webp'),
    ('Formations continues', '💼', ['formation-continue'], "Pour les professionnels : management, MBA et certifications.", 'img/campus/salle-de-cours-05.webp'),
]


def cycles_accueil():
    """Un bloc par cycle (classes prépas, BTS, licences, masters, formation continue) avec le nombre de formations."""
    out = []
    for titre, icone, slugs, desc, image in CYCLES:
        nb = Filiere.objects.filter(actif=True, niveaux__slug__in=slugs).distinct().count()
        if nb:
            out.append({'titre': titre, 'icone': icone, 'slugs': ','.join(slugs), 'description': desc, 'image': image, 'nb': nb})
    return out


def partenaires_defilants():
    """Liste répétée pour que la bande défilante soit toujours assez longue (même avec 2-3 partenaires)."""
    base = list(Partenaire.objects.filter(actif=True))
    if not base:
        return [], 0
    rep = -(-8 // len(base))                      # au moins ~8 logos par groupe
    return base * rep, len(base) * rep


def home(request):
    articles = list(Article.objects.filter(publie=True).select_related('categorie')[:3])
    return render(request, 'core/home.html', {
        'filieres': Filiere.objects.filter(actif=True, en_avant=True).prefetch_related('niveaux')[:6],
        'niveaux': niveaux_utilises_accueil(),
        'cycles': cycles_accueil(),
        'total_filieres': Filiere.objects.filter(actif=True).count(),
        'stats_barre': Chiffre.objects.filter(emplacement=Chiffre.BARRE),
        'stats_section': Chiffre.objects.filter(emplacement=Chiffre.SECTION),
        'valeurs': Valeur.objects.filter(zone=Valeur.ACCUEIL),
        'avantages': Valeur.objects.filter(zone=Valeur.POURQUOI),
        'partenaires': Partenaire.objects.filter(actif=True),
        'partenaires_boucle': partenaires_defilants()[0],
        'partenaires_duree': partenaires_defilants()[1] * 5,
        'article_une': articles[0] if articles else None,
        'articles_autres': articles[1:],
        'photos_campus': photos_accueil(),
        'form': DemandeAdmissionForm(),
    })


def rencontres_photos():
    album = Album.objects.filter(slug='rencontres-institutionnelles', actif=True).first()
    return list(album.photos.all()) if album else []


def apropos(request):
    return render(request, 'core/apropos.html', {
        'jalons': JalonHistoire.objects.all(),
        'valeurs': Valeur.objects.filter(zone=Valeur.APROPOS),
        'cycles': cycles_accueil(),
        'rencontres': rencontres_photos(),
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
