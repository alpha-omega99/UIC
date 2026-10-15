from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from apps.core.utils import validate_image


class Filiere(models.Model):
    nom = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    icone = models.CharField(max_length=8, blank=True)
    resume = models.CharField("Résumé (carte)", max_length=300)
    sous_titre = models.CharField(max_length=300, blank=True)
    description = models.TextField("À propos de la formation")
    licence = models.BooleanField(default=True)
    master = models.BooleanField(default=True)
    couleur_badge = models.CharField(max_length=7, default='#C8922A', help_text="Ex : #C8922A")
    duree = models.CharField(max_length=80)
    niveau_requis = models.CharField(max_length=120)
    mode = models.CharField(max_length=60, default="Présentiel + Hybride")
    langue = models.CharField(max_length=40, default="Français")
    debouches = models.TextField(blank=True, help_text="Un débouché par ligne")
    image = models.ImageField(upload_to='filieres/', blank=True, validators=[validate_image])
    image_url = models.URLField(blank=True, help_text="Image externe (utilisée si aucune image n'est téléversée)")
    ordre = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Filière"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('filieres:detail', args=[self.slug])

    @property
    def image_src(self):
        return self.image.url if self.image else self.image_url

    @property
    def niveaux_label(self):
        return ' · '.join(n for n, ok in (('Licence', self.licence), ('Master', self.master)) if ok)

    @property
    def niveaux_data(self):
        return ' '.join(n for n, ok in (('licence', self.licence), ('master', self.master)) if ok)

    @property
    def debouches_liste(self):
        return [l.strip() for l in self.debouches.splitlines() if l.strip()]


class Module(models.Model):
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='modules')
    semestre = models.PositiveSmallIntegerField()
    intitule = models.CharField(max_length=150)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['semestre', 'ordre', 'id']
        verbose_name = "Module"

    def __str__(self):
        return f"{self.filiere} — S{self.semestre} — {self.intitule}"
