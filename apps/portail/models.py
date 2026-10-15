from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from apps.core.storage import private_storage
from apps.core.utils import validate_document, validate_image, validate_phone
from apps.filieres.models import Filiere


class ProfilEtudiant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil_etudiant')
    matricule = models.CharField(max_length=20, unique=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True)
    niveau = models.CharField(max_length=30, blank=True, help_text="Ex : Licence 2")
    annee_inscription = models.PositiveSmallIntegerField()
    photo = models.ImageField(upload_to='etudiants/', blank=True, validators=[validate_image])
    telephone = models.CharField(max_length=25, blank=True, validators=[validate_phone])

    class Meta:
        verbose_name = "Profil étudiant"
        verbose_name_plural = "Profils étudiants"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.matricule})"


class Resultat(models.Model):
    SESSIONS = [('normale', 'Session normale'), ('rattrapage', 'Rattrapage')]
    etudiant = models.ForeignKey(ProfilEtudiant, on_delete=models.CASCADE, related_name='resultats')
    matiere = models.CharField(max_length=150)
    note = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    note_max = models.DecimalField(max_digits=4, decimal_places=2, default=20, validators=[MinValueValidator(Decimal('1'))])
    semestre = models.PositiveSmallIntegerField()
    annee_academique = models.CharField(max_length=9, help_text="Ex : 2025-2026")
    session = models.CharField(max_length=10, choices=SESSIONS, default='normale')
    publie = models.BooleanField(default=False)

    class Meta:
        ordering = ['-annee_academique', 'semestre', 'matiere']
        verbose_name = "Résultat d'examen"
        verbose_name_plural = "Résultats d'examens"

    def __str__(self):
        return f"{self.etudiant.matricule} — {self.matiere}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.note is not None and self.note_max is not None and self.note > self.note_max:
            raise ValidationError("La note ne peut pas dépasser la note maximale.")

    @property
    def sur_20(self):
        return float(self.note) / float(self.note_max) * 20

    @property
    def mention(self):
        n = self.sur_20
        return 'Très bien' if n >= 16 else 'Bien' if n >= 14 else 'Assez bien' if n >= 12 else 'Passable' if n >= 10 else 'Insuffisant'

    @property
    def mention_css(self):
        return 'ok' if self.sur_20 >= 12 else 'mid' if self.sur_20 >= 10 else 'ko'


class CarteAdmission(models.Model):
    etudiant = models.ForeignKey(ProfilEtudiant, on_delete=models.CASCADE, related_name='cartes')
    titre = models.CharField(max_length=150, help_text="Ex : Examens de fin de semestre 1")
    annee_academique = models.CharField(max_length=9)
    date_examen = models.DateField(null=True, blank=True)
    salle = models.CharField(max_length=60, blank=True)
    fichier = models.FileField(upload_to='cartes/', storage=private_storage, validators=[validate_document])
    publie = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Carte d'admission (Admit Card)"
        verbose_name_plural = "Cartes d'admission (Admit Card)"

    def __str__(self):
        return f"{self.etudiant.matricule} — {self.titre}"


class Certificat(models.Model):
    TYPES = [('scolarite', 'Certificat de scolarité'), ('inscription', "Attestation d'inscription"),
             ('reussite', 'Attestation de réussite'), ('autre', 'Autre document')]
    etudiant = models.ForeignKey(ProfilEtudiant, on_delete=models.CASCADE, related_name='certificats')
    type_document = models.CharField(max_length=12, choices=TYPES)
    annee_academique = models.CharField(max_length=9)
    fichier = models.FileField(upload_to='certificats/', storage=private_storage, validators=[validate_document])
    publie = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Certificat"

    def __str__(self):
        return f"{self.etudiant.matricule} — {self.get_type_document_display()}"
