from django.contrib import admin
from .models import DemandeAdmission


@admin.register(DemandeAdmission)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ('numero_dossier', 'prenom', 'nom', 'filiere', 'niveau_entree', 'statut', 'created_at')
    list_editable = ('statut',)
    list_filter = ('statut', 'filiere', 'niveau_entree')
    search_fields = ('prenom', 'nom', 'email', 'numero_dossier')
    readonly_fields = ('numero_dossier', 'created_at', 'updated_at')
