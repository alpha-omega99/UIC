# Images du site — organisation

```
static/img/
├── marque/          logo (logo.webp)
├── accueil/         images de la page d'accueil (étudiante du hero, président, affiche des formations)
├── affiches/        affiches et bannières (formations BTS/Licences/Master, concours classe prépa)
├── campus/          vie-etudiante-XX, travail-en-groupe-XX, salle-de-cours-XX
├── evenements/      remise-diplomes-XX, journee-culturelle-XX
├── partenaires/     logos des universités partenaires
└── placeholders/    image par défaut (photo-defaut.webp)
```

## Règles
- Format **WebP**, largeur max **1600 px** (1920 px pour les bannières larges), qualité ~80 : le site reste rapide sur téléphone.
- Noms en minuscules, sans espaces ni accents : `categorie-numero.webp`.
- Un seul fichier par image : pas de doublons à plusieurs tailles.

## Où chaque image est utilisée
Les associations sont dans `apps/core/data/images.json` (filières, actualités, albums de la galerie, partenaires).
Après modification : `python manage.py seed_images` (ne remplace jamais une image choisie dans l'administration).

## Ajouter une image
1. Copier le fichier (WebP) dans le bon dossier.
2. Dans l'administration, remplir le champ « Image du site » avec le chemin, ex. `img/campus/salle-de-cours-05.webp`
   (ou téléverser le fichier, mais les fichiers téléversés sont perdus à chaque redéploiement sur Render gratuit).

## Partenaires
Les trois logos actuels sont des **recadrages provisoires** de l'affiche des formations (basse résolution).
Remplacer par les logos officiels : mêmes noms de fichiers dans `partenaires/`, de préférence en PNG/WebP fond transparent d'au moins 400 px de large.

## Ajouts « vie du campus »
- `campus/vie-etudiante-11..14.webp` : portraits et groupes d'étudiants
- `campus/salle-de-cours-05.webp`, `salle-de-cours-06.webp` : étudiants en salle de cours
- `campus/batiment-01..03.webp` : bâtiment du campus (basse résolution, 680 px : à remplacer par les originaux)
- `evenements/stand-uic-01.webp` : stand de l'UIC
Ces photos sont reliées aux albums par `python manage.py seed_images` (voir `apps/core/data/images.json`).
