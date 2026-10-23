# Lancement officiel du site UIC (branche `production`)

## 0. Avant tout : SAUVEGARDER (2 minutes)
Chaque fois avant de fusionner, migrer ou déployer :
```
python manage.py sauvegarder_donnees
```
→ crée `sauvegardes/uic-AAAAMMJJ-HHMM.json.gz` (toute la base : formations, actualités, pré-inscriptions, messages, comptes). Ce dossier n'est jamais envoyé sur GitHub.
Restaurer (dans une base vide, après `migrate`) : décompresser le fichier puis `python manage.py loaddata uic-....json`.
Copier aussi le dossier `media/` (photos ajoutées depuis l'administration).
Sauvegarde native PostgreSQL (si `pg_dump` est installé) :
```
pg_dump "$DATABASE_URL" -Fc -f sauvegardes/uic-$(date +%Y%m%d).dump
```
Sur Render, la base GRATUITE n'a aucune sauvegarde et expire après 30 jours (14 jours de grâce avant suppression) : sauvegarder avant l'échéance.
Base payante : sauvegardes logiques conservées 7 jours (téléchargeables) + restauration à un instant précis (3 jours Hobby, 7 jours Pro).

## 0 bis. Fusionner `nouvelles-formations` dans `main`
```
git checkout nouvelles-formations
git add -A && git commit -m "Nouvelles formations, accueil, actualités, admission"
git push -u origin nouvelles-formations
git checkout main
git pull
git merge nouvelles-formations
git push
```
`main` redéploie la démo : `build.sh` applique les migrations et charge les nouveautés une seule fois. Vérifier la démo, puis créer/mettre à jour `production` (section 1).
Si `render.yaml` apparaît supprimé : `git restore render.yaml`.

La branche **main** = démonstration (hébergement gratuit, contenu de démo).
La branche **production** = site officiel (hébergement payant, données authentiques).
Le code est le même ; seuls `render.yaml` et les variables Render changent. Il suffit donc de fusionner `main` dans `production` pour recevoir les corrections.

## 1. Créer la branche (une seule fois)
```
git checkout main
git pull
git checkout -b production
cp render.production.yaml render.yaml
git add render.yaml
git commit -m "production: render.yaml payant"
git push -u origin production
git checkout main
```
Ensuite, pour mettre la production à jour avec les corrections faites sur main :
```
git checkout production
git merge main        # en cas de conflit sur render.yaml : garder la version production
git push
git checkout main
```

## 2. Comptes à ouvrir AU NOM DE L'UIC
1. Compte Render de l'UIC, avec sa carte de paiement. Ajouter le développeur comme membre de l'équipe.
2. Nom de domaine `uic-ci.org` (nouveau domaine choisi par le fondateur) : vérifier qui le détient et où il est géré.

## 3. Base de données payante
Render > New > PostgreSQL > plan payant (Basic) > région Frankfurt si disponible (la plus proche d'Abidjan), puis copier l'**Internal Database URL**.
Choisir la **même région** que le service web.

## 4. Service web
Render > New > Blueprint > dépôt `alpha-omega99/UIC` > branche `production` > fichier `render.yaml`.
Saisir : DATABASE_URL, ADMIN_URL (ex. `gestion-uic-k7x2/`), compte administrateur, e-mails.
Le premier déploiement charge seulement les 19 formations réelles (SEED_MODE=production).

## 5. Domaine
Render > service > Settings > Custom Domains > ajouter `uic-ci.org` et `www.uic-ci.org`, puis créer chez le registraire les enregistrements DNS indiqués par Render.
`ALLOWED_HOSTS` contient déjà les deux domaines.

## 6. Contenu authentique à saisir dans l'administration (rien n'est inventé)
- Informations de l'établissement : forme juridique, RCCM, numéro d'agrément, directeur de la publication, année de fondation, **vérifier la phrase d'agrément du pied de page** et les horaires, téléphone, adresse.
- Mot du Président : nom, citation, texte, et remplacer la photo `static/img/accueil/president.webp` si besoin (la section n'apparaît que si le texte est rempli).
- Chiffres clés, valeurs, jalons d'histoire, FAQ : uniquement des données confirmées par l'UIC (les sections vides sont masquées).
- Actualités : vrais articles.
- Formations : relire chaque fiche (durées, conditions d'accès, débouchés) ; les champs « Nous consulter » sont à compléter.
- Photos : vérifier le droit à l'image ; remplacer les photos de basse résolution par les originaux.
- Logos des partenaires : fichiers officiels (les actuels sont des recadrages provisoires).

## 6 bis. Corrections demandées par le fondateur
Voir `CORRECTIONS.md` : un seul fichier `apps/core/data/corrections.csv`, appliqué automatiquement au déploiement.

## 7. Avant d'annoncer le site
- [ ] Pré-inscription de test reçue par e-mail à l'adresse de l'UIC (NOTIFY_EMAIL)
- [ ] Formulaire de contact testé
- [ ] HTTPS actif sur `uic-ci.org` et `www.uic-ci.org`
- [ ] Sauvegarde de la base activée dans Render (plan payant) et restauration testée
- [ ] Pages légales relues par l'UIC
- [ ] Mot de passe administrateur fort, enregistré dans un gestionnaire
- [ ] Renouvellements notés : domaine, hébergement

## E-mails des formulaires (admission + contact)

Chaque soumission est **enregistrée dans l'admin ET envoyée par e-mail** à `NOTIFY_EMAIL`
(plusieurs adresses possibles, séparées par des virgules). Si l'envoi échoue, la soumission reste dans l'admin
et l'erreur apparaît dans les logs Render.

Variables Render (Environment) :
- `NOTIFY_EMAIL` = adresse(s) de réception, ex. `info@uic-ci.org`
- **Option A – Gmail/SMTP** (hébergement PAYANT uniquement) : `EMAIL_HOST_USER` = adresse Gmail,
  `EMAIL_HOST_PASSWORD` = *mot de passe d'application* Gmail (validation en 2 étapes requise).
- **Option B – Brevo (API HTTPS)**, marche aussi sur l'offre gratuite : `BREVO_API_KEY` (compte gratuit Brevo,
  expéditeur validé) + `DEFAULT_FROM_EMAIL` = `UIC <adresse validée dans Brevo>`.

Render bloque le SMTP (ports 25/465/587) sur les services web gratuits depuis septembre 2025.
