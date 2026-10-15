from django.contrib import admin
from .models import CarteAdmission, Certificat, ProfilEtudiant, Resultat


class ResultatInline(admin.TabularInline):
    model = Resultat
    extra = 0


@admin.register(ProfilEtudiant)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'filiere', 'niveau', 'annee_inscription')
    list_filter = ('filiere', 'annee_inscription')
    search_fields = ('matricule', 'user__username', 'user__first_name', 'user__last_name')
    autocomplete_fields = ()
    raw_id_fields = ('user',)
    inlines = [ResultatInline]


@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'matiere', 'note', 'note_max', 'semestre', 'annee_academique', 'publie')
    list_editable = ('publie',)
    list_filter = ('annee_academique', 'semestre', 'session', 'publie')
    search_fields = ('etudiant__matricule', 'matiere')


@admin.register(CarteAdmission)
class CarteAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'titre', 'annee_academique', 'date_examen', 'publie')
    list_editable = ('publie',)
    search_fields = ('etudiant__matricule', 'titre')


@admin.register(Certificat)
class CertificatAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'type_document', 'annee_academique', 'publie')
    list_editable = ('publie',)
    search_fields = ('etudiant__matricule',)
