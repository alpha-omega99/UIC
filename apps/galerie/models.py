from django.db import models
from django.utils.text import slugify
from apps.core.utils import validate_image


class Album(models.Model):
    titre = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.CharField(max_length=300, blank=True)
    date = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date', '-id']
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
        return p.image.url if p else ''


class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='galerie/', validators=[validate_image])
    legende = models.CharField(max_length=150, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Photo"

    def __str__(self):
        return self.legende or f"Photo {self.pk}"
