from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from apps.core.utils import image_source, validate_image


class Categorie(models.Model):
    nom = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name = "Catégorie"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Article(models.Model):
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='articles')
    titre = models.CharField(max_length=250)
    slug = models.SlugField(max_length=270, unique=True, blank=True)
    chapeau = models.CharField(max_length=400, blank=True)
    contenu = models.TextField(help_text="Séparez les paragraphes par une ligne vide.")
    image = models.ImageField(upload_to='articles/', blank=True, validators=[validate_image])
    image_statique = models.CharField("Image du site", max_length=200, blank=True, help_text="Chemin dans static/, ex : img/evenements/remise-diplomes-01.webp")
    image_url = models.URLField(blank=True)
    temps_lecture = models.PositiveSmallIntegerField(default=3, help_text="minutes")
    publie = models.BooleanField(default=False)
    date_publication = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date_publication']
        verbose_name = "Actualité"
        verbose_name_plural = "Actualités"

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre)[:270]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('actualites:detail', args=[self.slug])

    @property
    def image_src(self):
        return image_source(self.image, self.image_statique, self.image_url)

    @property
    def paragraphes(self):
        return [p.strip() for p in self.contenu.split('\n\n') if p.strip()]
