from django.db import models
from apps.core.utils import image_source, validate_image


class Professeur(models.Model):
    prenom = models.CharField(max_length=80)
    nom = models.CharField(max_length=80)
    titre = models.CharField(max_length=120, blank=True, help_text="Ex : Docteur en Droit, Directeur du département…")
    specialite = models.CharField(max_length=160, blank=True)
    photo = models.ImageField(upload_to='professeurs/', blank=True, validators=[validate_image])
    photo_statique = models.CharField("Photo du site", max_length=200, blank=True, help_text="Chemin dans static/, ex : img/enseignants/nom.webp")
    biographie = models.TextField(blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Enseignant"

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    @property
    def photo_src(self):
        return image_source(self.photo, self.photo_statique)
