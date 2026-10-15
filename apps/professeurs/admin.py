from django.contrib import admin
from .models import Professeur


@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'titre', 'specialite', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')
