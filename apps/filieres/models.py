from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from apps.core.utils import image_source, validate_image


class NiveauFormation(models.Model):
    """Type de diplôme / cycle : Licence, Master, BTS, Classe préparatoire, Formation continue…
    Les filtres du site sont générés à partir de cette liste : ajouter un niveau ici suffit."""
    nom = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Niveau de formation"
        verbose_name_plural = "Niveaux de formation"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


class Pole(models.Model):
    """École / département qui regroupe des formations (ex : École de droit, Département Gestion).
    Sert à ranger le catalogue quand il y a beaucoup de formations. Facultatif."""
    nom = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.CharField(max_length=300, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "École / département"
        verbose_name_plural = "Écoles / départements"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


class Filiere(models.Model):
    nom = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    icone = models.CharField(max_length=8, blank=True)
    resume = models.CharField("Résumé (carte)", max_length=300)
    sous_titre = models.CharField(max_length=300, blank=True)
    description = models.TextField("À propos de la formation")
    pole = models.ForeignKey(Pole, null=True, blank=True, on_delete=models.SET_NULL, related_name='filieres',
                             verbose_name="École / département", help_text="Facultatif : range la formation dans le catalogue.")
    niveaux = models.ManyToManyField(NiveauFormation, blank=True, related_name='filieres', verbose_name="Niveaux",
                                     help_text="Ex : Licence + Master. Les filtres du site s'ajustent automatiquement.")
    en_avant = models.BooleanField("Afficher sur l'accueil", default=True,
                                   help_text="Décocher pour ne montrer cette formation que sur la page « Filières ».")
    couleur_badge = models.CharField(max_length=7, default='#C8922A', help_text="Ex : #C8922A")
    duree = models.CharField(max_length=80)
    niveau_requis = models.CharField(max_length=120)
    mode = models.CharField(max_length=60, blank=True)
    langue = models.CharField(max_length=40, default="Français")
    debouches = models.TextField(blank=True, help_text="Un débouché par ligne")
    image = models.ImageField(upload_to='filieres/', blank=True, validators=[validate_image])
    image_statique = models.CharField("Image du site", max_length=200, blank=True, help_text="Chemin dans static/, ex : img/campus/vie-etudiante-01.webp")
    image_url = models.URLField(blank=True, help_text="Image externe (utilisée si aucune autre image)")
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
        return image_source(self.image, self.image_statique, self.image_url)

    @property
    def niveaux_label(self):
        return ' · '.join(n.nom for n in self.niveaux.all())

    @property
    def niveaux_data(self):
        return ' '.join(n.slug for n in self.niveaux.all())

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
