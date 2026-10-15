from django.db import models
from apps.core.utils import validate_phone

SUJETS = [("admission", "Demande d'admission"), ("filiere", "Informations sur une filière"),
          ("partenariat", "Partenariat entreprise"), ("autre", "Autre demande")]


class MessageContact(models.Model):
    prenom = models.CharField(max_length=80)
    nom = models.CharField(max_length=80)
    email = models.EmailField()
    telephone = models.CharField(max_length=25, blank=True, validators=[validate_phone])
    sujet = models.CharField(max_length=15, choices=SUJETS)
    message = models.TextField(max_length=2000)
    lu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message reçu"
        verbose_name_plural = "Messages reçus"

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.get_sujet_display()}"
