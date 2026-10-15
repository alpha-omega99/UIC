import secrets
from django.db import models
from django.utils import timezone
from apps.core.utils import validate_phone
from apps.filieres.models import Filiere

NIVEAUX = [
    ('bac-l1', 'Baccalauréat → Licence 1'),
    ('bac2-l3', 'Bac+2 → Licence 3'),
    ('l-m1', 'Licence → Master 1'),
    ('m1-m2', 'Master 1 → Master 2'),
]


class DemandeAdmission(models.Model):
    STATUTS = [('en_attente', 'En attente'), ('en_cours', "En cours d'examen"),
               ('accepte', 'Accepté'), ('refuse', 'Refusé'), ('incomplet', 'Dossier incomplet')]
    prenom = models.CharField(max_length=80)
    nom = models.CharField(max_length=80)
    email = models.EmailField()
    telephone = models.CharField(max_length=25, blank=True, validators=[validate_phone])
    filiere = models.ForeignKey(Filiere, on_delete=models.PROTECT, related_name='candidatures')
    niveau_entree = models.CharField(max_length=10, choices=NIVEAUX)
    statut = models.CharField(max_length=12, choices=STATUTS, default='en_attente')
    numero_dossier = models.CharField(max_length=20, unique=True, editable=False)
    note_interne = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Demande d'admission"
        verbose_name_plural = "Demandes d'admission"

    def __str__(self):
        return f"{self.numero_dossier} — {self.prenom} {self.nom}"

    def save(self, *args, **kwargs):
        if not self.numero_dossier:
            # Numéro NON séquentiel : impossible à deviner/énumérer
            for _ in range(10):
                n = f"UIC-{timezone.now():%Y}-{secrets.token_hex(3).upper()}"
                if not DemandeAdmission.objects.filter(numero_dossier=n).exists():
                    self.numero_dossier = n
                    break
        super().save(*args, **kwargs)
