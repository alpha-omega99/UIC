from django.core.exceptions import ValidationError
from django.db import models

from .utils import image_source, validate_image


def _maps_ok(value):
    if value and not value.startswith('https://www.google.com/maps/embed'):
        raise ValidationError("Utilisez le lien « Intégrer une carte » de Google Maps (https://www.google.com/maps/embed...).")


class InfoEtablissement(models.Model):
    """Réglages généraux du site (une seule ligne)."""
    nom = models.CharField(max_length=200, default="Université Internationale de Cocody")
    nom_court = models.CharField(max_length=20, default="UIC")
    annee_fondation = models.PositiveSmallIntegerField(default=2004)
    # Hero
    hero_surtitre = models.CharField("Hero : surtitre", max_length=120, default="Campus de Cocody, Abidjan")
    hero_titre_debut = models.CharField("Hero : titre (début)", max_length=120, default="L'UIC forme ceux qui")
    hero_titre_accent = models.CharField("Hero : titre (partie dorée)", max_length=80, default="font bouger")
    hero_titre_fin = models.CharField("Hero : titre (fin)", max_length=120, default="la Côte d'Ivoire")
    hero_description = models.TextField("Hero : description", default="")
    slogan_splash = models.CharField(max_length=200, default="Abidjan forme ses décideurs depuis 2004.")
    texte_footer = models.TextField(default="")
    agrement = models.CharField(max_length=200, default="Établissement agréé par le Ministère de l'Enseignement Supérieur")
    # Mot du Président
    president_nom = models.CharField(max_length=120, default="Le Président")
    president_citation = models.TextField(default="")
    president_texte = models.TextField(default="")
    # Contact
    telephone = models.CharField(max_length=30, default="(+225) 07 78 63 74 00", validators=[])
    email = models.EmailField(default="uicinfos@gmail.com")
    whatsapp = models.CharField("WhatsApp (chiffres seulement)", max_length=20, default="2250778637400")
    adresse = models.CharField(max_length=250, default="Cocody Deux-Plateaux, Angé 7ième Tranche, Abidjan")
    boite_postale = models.CharField(max_length=100, default="04 BP 2268 Abidjan 04")
    horaires = models.CharField(max_length=120, default="Lundi – Vendredi : 10h00 – 16h00")
    horaires_court = models.CharField(max_length=60, default="Lun–Ven : 10h–16h")
    maps_embed = models.URLField(max_length=700, blank=True, validators=[_maps_ok])
    # Mentions légales (affichées uniquement si renseignées)
    statut_juridique = models.CharField("Forme juridique", max_length=160, blank=True, help_text="Ex : Société à responsabilité limitée (SARL), association…")
    rccm = models.CharField("N° RCCM / immatriculation", max_length=80, blank=True)
    numero_agrement = models.CharField("N° d'agrément / arrêté d'ouverture", max_length=120, blank=True)
    directeur_publication = models.CharField("Directeur de la publication", max_length=120, blank=True)
    hebergeur = models.CharField("Hébergeur du site", max_length=250,
                                 default="Render Services, Inc. — 525 Brannan Street, Suite 300, San Francisco, CA 94107, États-Unis (render.com)")
    facebook = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    x_twitter = models.URLField("X (Twitter)", blank=True)
    youtube = models.URLField(blank=True)

    class Meta:
        verbose_name = "Informations de l'établissement"
        verbose_name_plural = "Informations de l'établissement"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # singleton : non supprimable
        pass

    @property
    def telephone_lien(self):
        return '+' + ''.join(c for c in self.telephone if c.isdigit())

    @classmethod
    def get(cls):
        return cls.objects.get_or_create(pk=1)[0]


class Chiffre(models.Model):
    BARRE, SECTION = 'barre', 'section'
    EMPLACEMENTS = [(BARRE, "Barre sous le hero"), (SECTION, "Section « chiffres »")]
    emplacement = models.CharField(max_length=10, choices=EMPLACEMENTS)
    icone = models.CharField(max_length=8, blank=True, help_text="Emoji (barre uniquement)")
    valeur = models.PositiveIntegerField()
    suffixe = models.CharField(max_length=10, blank=True, help_text="Ex : + ou % ou « ans »")
    libelle = models.CharField(max_length=80)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['emplacement', 'ordre']
        verbose_name = "Chiffre clé"
        verbose_name_plural = "Chiffres clés"

    def __str__(self):
        return f"{self.valeur}{self.suffixe} {self.libelle}"


class Valeur(models.Model):
    ACCUEIL, APROPOS, POURQUOI = 'accueil', 'apropos', 'pourquoi'
    ZONES = [(ACCUEIL, "Accueil — présentation"), (APROPOS, "Page À propos — valeurs"), (POURQUOI, "Accueil — « Pourquoi nous choisir »")]
    zone = models.CharField(max_length=10, choices=ZONES)
    icone = models.CharField(max_length=8)
    titre = models.CharField(max_length=80)
    texte = models.TextField()
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['zone', 'ordre']
        verbose_name = "Valeur / avantage"
        verbose_name_plural = "Valeurs & avantages"

    def __str__(self):
        return f"[{self.get_zone_display()}] {self.titre}"


class JalonHistoire(models.Model):
    annee = models.CharField(max_length=10)
    titre = models.CharField(max_length=120)
    texte = models.TextField()

    class Meta:
        ordering = ['annee']
        verbose_name = "Jalon de l'histoire"
        verbose_name_plural = "Histoire de l'UIC (frise)"

    def __str__(self):
        return f"{self.annee} — {self.titre}"


class FAQ(models.Model):
    question = models.CharField(max_length=250)
    reponse = models.TextField()
    ordre = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Question fréquente"
        verbose_name_plural = "Questions fréquentes (FAQ)"

    def __str__(self):
        return self.question


class Partenaire(models.Model):
    nom = models.CharField(max_length=120)
    pays = models.CharField(max_length=80, blank=True)
    logo = models.ImageField("Logo (téléversé)", upload_to='partenaires/', blank=True, validators=[validate_image])
    logo_statique = models.CharField("Logo du site", max_length=200, blank=True,
                                     help_text="Chemin dans static/, ex : img/partenaires/universite-laval.webp")
    site_web = models.URLField(blank=True, help_text="Lien vers le site du partenaire (https://…)")
    ordre = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Partenaire"

    def __str__(self):
        return self.nom

    @property
    def logo_src(self):
        return image_source(self.logo, self.logo_statique)
