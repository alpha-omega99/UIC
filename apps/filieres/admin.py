from django.contrib import admin

from .models import Filiere, Module, NiveauFormation, Pole


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 2


@admin.register(NiveauFormation)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ordre')
    list_editable = ('ordre',)
    prepopulated_fields = {'slug': ('nom',)}


@admin.register(Pole)
class PoleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ordre')
    list_editable = ('ordre',)
    prepopulated_fields = {'slug': ('nom',)}


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pole', 'niveaux_label', 'duree', 'en_avant', 'ordre', 'actif')
    list_editable = ('en_avant', 'ordre', 'actif')
    list_filter = ('pole', 'niveaux', 'actif', 'en_avant', 'nouveau')
    search_fields = ('nom', 'resume')
    filter_horizontal = ('niveaux',)
    prepopulated_fields = {'slug': ('nom',)}
    inlines = [ModuleInline]
    fieldsets = (
        ('Identité', {'fields': ('nom', 'slug', 'icone', 'pole', 'niveaux', 'resume', 'sous_titre', 'description')}),
        ('Informations pratiques', {'fields': ('duree', 'niveau_requis', 'mode', 'langue', 'debouches')}),
        ('Fiche détaillée (facultative)', {'classes': ('collapse',), 'fields': (
            'objectif', 'public_cible', 'organisation', 'programme', 'competences', 'atouts', 'admission', 'frais',
            'repere_salaire', 'accroche', 'licence_associee')}),
        ('Image', {'fields': ('image_statique', 'image', 'image_url')}),
        ('Affichage', {'fields': ('couleur_badge', 'nouveau', 'en_avant', 'ordre', 'actif')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pole').prefetch_related('niveaux')

    @admin.display(description="Niveaux")
    def niveaux_label(self, obj):
        return obj.niveaux_label
