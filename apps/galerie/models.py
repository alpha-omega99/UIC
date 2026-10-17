from django.db import models
from django.utils.text import slugify
from apps.core.utils import image_source, validate_image


class Album(models.Model):
    titre = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.CharField(max_length=300, blank=True)
    date = models.DateField(null=True, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0, help_text="Position dans la galerie (0 = en premier).")
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', '-date', '-id']
        verbose_name = "Album photo"

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre)
        super().save(*args, **kwargs)

    @property
    def couverture(self):
        p = self.photos.first()
        return p.image_src if p else ''


class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='galerie/', blank=True, validators=[validate_image])
    image_statique = models.CharField("Image du site", max_length=200, blank=True, help_text="Chemin dans static/, ex : img/campus/salle-de-cours-01.webp")
    legende = models.CharField(max_length=150, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Photo"

    def __str__(self):
        return self.legende or f"Photo {self.pk}"

    @property
    def image_src(self):
        return image_source(self.image, self.image_statique)
