# UIC – Site web Django (Université Internationale de Cocody)

Design d'origine (marine/or, Cormorant Garamond + Inter) + fonctionnalités : filières, actualités, galerie, enseignants,
pré-inscription en ligne avec suivi de dossier, contact, espace étudiant (résultats, cartes d'admission, certificats), FAQ.

## Lancer en local
```bash
python -m venv venv && source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # puis mettre une SECRET_KEY aléatoire (voir ci-dessous)
python manage.py migrate
python manage.py createcachetable
python manage.py seed_uic                            # contenu de la maquette
python manage.py createsuperuser
python manage.py runserver
```
Clé secrète : `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`
Administration : `http://127.0.0.1:8000/<ADMIN_URL>` (par défaut `gestion-uic/`, à changer dans `.env`).
Espace étudiant : créer un utilisateur + un « Profil étudiant » dans l'admin (`seed_uic --demo-etudiant` crée un compte de démo, à ne PAS utiliser en production).

## PostgreSQL (recommandé)
Sans `DATABASE_URL`, le projet utilise SQLite. Avec, il utilise PostgreSQL :
```sql
-- dans psql (utilisateur postgres)
CREATE USER uic_user WITH PASSWORD 'un_mot_de_passe_solide' CREATEDB;
CREATE DATABASE uic_db OWNER uic_user ENCODING 'UTF8';
```
Puis dans `.env` : `DATABASE_URL=postgres://uic_user:un_mot_de_passe_solide@localhost:5432/uic_db`
(caractères spéciaux du mot de passe : les encoder, ex. `@` → `%40`), et relancer `migrate`, `createcachetable`, `seed_uic`.

## Tests
`python manage.py test`

## Déploiement sur Render
1. Pousser le projet sur GitHub, puis « New + > Blueprint » : Render lit `render.yaml`.
2. Variables à renseigner : `ALLOWED_HOSTS` (votre domaine), `ADMIN_URL` (secret), `EMAIL_*` (SMTP), `CSRF_TRUSTED_ORIGINS` (https://votre-domaine).
3. **Base de données** : `render.yaml` crée une base PostgreSQL (`uic-db`) et branche `DATABASE_URL`. Attention : la base gratuite de Render expire après un certain délai ; prévoir une offre payante pour la production. **Fichiers téléversés** : le disque persistant (payant, `/var/data`) est configuré pour `media/` ; sans lui, les fichiers sont perdus à chaque déploiement.
4. Après le premier déploiement : ouvrir le Shell Render → `python manage.py createsuperuser` puis `python manage.py seed_uic`.

## Sécurité (résumé)
CSP stricte (pas de script inline), HSTS/SSL/cookies sécurisés en production, limitation de débit (inscription, contact, connexion, réinitialisation), honeypot anti-spam,
n° de dossier non devinables, messages de connexion génériques, déconnexion en POST, isolation des données par étudiant,
documents privés servis uniquement après authentification (hors `MEDIA_ROOT`), URL d'admin personnalisée, validation des fichiers, protection contre l'open redirect et l'injection d'en-têtes e-mail.
