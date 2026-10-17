from django.contrib import admin
from .models import FAQ, Chiffre, InfoEtablissement, JalonHistoire, Partenaire, Valeur


@admin.register(InfoEtablissement)
class InfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Identité', {'fields': ('nom', 'nom_court', 'annee_fondation', 'agrement', 'slogan_splash', 'texte_footer')}),
        ('Page d\'accueil (hero)', {'fields': ('hero_surtitre', 'hero_titre_debut', 'hero_titre_accent', 'hero_titre_fin', 'hero_description')}),
        ('Mot du Président', {'fields': ('president_nom', 'president_citation', 'president_texte')}),
        ('Contact', {'fields': ('telephone', 'email', 'whatsapp', 'adresse', 'boite_postale', 'horaires', 'horaires_court', 'maps_embed')}),
        ('Mentions légales', {'fields': ('statut_juridique', 'rccm', 'numero_agrement', 'directeur_publication', 'hebergeur'),
                              'description': "Ces informations apparaissent dans la page « Mentions légales ». Les champs vides ne sont pas affichés."}),
        ('Réseaux sociaux', {'fields': ('facebook', 'linkedin', 'x_twitter', 'youtube')}),
    )

    def has_add_permission(self, request):
        return not InfoEtablissement.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Chiffre)
class ChiffreAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'valeur', 'suffixe', 'emplacement', 'ordre')
    list_editable = ('ordre',)
    list_filter = ('emplacement',)


@admin.register(Valeur)
class ValeurAdmin(admin.ModelAdmin):
    list_display = ('titre', 'zone', 'ordre')
    list_editable = ('ordre',)
    list_filter = ('zone',)


@admin.register(JalonHistoire)
class JalonAdmin(admin.ModelAdmin):
    list_display = ('annee', 'titre')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'actif', 'ordre')
    list_editable = ('actif', 'ordre')


@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pays', 'actif', 'ordre')
    list_editable = ('actif', 'ordre')
