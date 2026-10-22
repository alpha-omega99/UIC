"""Applique en une fois les corrections de contenu demandées par l'UIC (chiffres, histoire, valeurs, FAQ, textes…).

Les corrections sont écrites dans UN fichier tableur : apps/core/data/corrections.csv
(5 colonnes : cible ; repere ; action ; champ ; nouvelle_valeur — voir CORRECTIONS.md).

* Chaque ligne n'est appliquée qu'UNE fois (mémorisée en base) : relancer la commande, ou redéployer, ne réécrit
  donc jamais une modification faite ensuite dans l'administration.
* Une ligne modifiée dans le fichier est considérée comme une nouvelle correction et s'applique.
* Une ligne qui pose problème est signalée (numéro de ligne) et ignorée : le reste est appliqué, le déploiement n'échoue jamais.

Usage :
    python manage.py appliquer_corrections --simuler     # montre ce qui changerait, sans rien écrire
    python manage.py appliquer_corrections               # applique
"""
import csv
import hashlib
import io
import unicodedata
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import models, transaction

from apps.actualites.models import Article, Categorie
from apps.core.models import FAQ, Chiffre, CorrectionAppliquee, InfoEtablissement, JalonHistoire, Partenaire, Valeur
from apps.filieres.models import Filiere

FICHIER = Path(__file__).resolve().parents[2] / 'data' / 'corrections.csv'

# cible -> (modèle, champ qui sert de repère, champ de filtre après « @ », libellé)
CIBLES = {
    'info': (InfoEtablissement, None, None, "Informations de l'établissement"),
    'chiffre': (Chiffre, 'libelle', 'emplacement', 'Chiffre clé'),
    'valeur': (Valeur, 'titre', 'zone', 'Valeur / avantage'),
    'jalon': (JalonHistoire, 'annee', None, "Jalon de l'histoire"),
    'faq': (FAQ, 'question', None, 'Question fréquente'),
    'article': (Article, 'titre', None, 'Actualité'),
    'filiere': (Filiere, 'nom', None, 'Formation'),
    'partenaire': (Partenaire, 'nom', None, 'Partenaire'),
}
ALIAS_CIBLES = {'infos': 'info', 'établissement': 'info', 'etablissement': 'info', 'chiffres': 'chiffre', 'valeurs': 'valeur',
                'jalons': 'jalon', 'histoire': 'jalon', 'articles': 'article', 'actualite': 'article', 'actualité': 'article',
                'formation': 'filiere', 'filière': 'filiere', 'partenaires': 'partenaire'}
ACTIONS = {'': 'modifier', 'modifier': 'modifier', 'changer': 'modifier', 'ajouter': 'ajouter', 'creer': 'ajouter', 'créer': 'ajouter',
           'supprimer': 'supprimer', 'retirer': 'supprimer'}
INTERDITS = {'id', 'slug', 'date_publication', 'singleton'}


def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return ' '.join(s.split())


def champs_modifiables(modele):
    out = {}
    for f in modele._meta.get_fields():
        if not getattr(f, 'concrete', False) or f.primary_key or f.name in INTERDITS:
            continue
        if isinstance(f, (models.ImageField, models.FileField, models.ManyToManyField)):
            continue
        out[norm(f.name)] = f
    return out


def convertir(champ, valeur):
    v = valeur.strip()
    if isinstance(champ, models.BooleanField):
        if norm(v) in ('oui', 'vrai', '1', 'true', 'o', 'x'):
            return True
        if norm(v) in ('non', 'faux', '0', 'false', 'n'):
            return False
        raise ValueError(f"« {valeur} » : écrire oui ou non")
    if isinstance(champ, models.IntegerField):
        return int(v.replace(' ', '').replace(' ', ''))
    if isinstance(champ, models.ForeignKey) and champ.related_model is Categorie:
        return Categorie.objects.get_or_create(nom=v)[0]
    if getattr(champ, 'choices', None):
        for cle, lib in champ.choices:
            if norm(v) in (norm(cle), norm(lib)):
                return cle
        raise ValueError(f"« {valeur} » : valeurs possibles : " + ', '.join(str(c) for c, _ in champ.choices))
    return v


def lire_lignes(texte):
    texte = texte.lstrip('﻿')
    lignes = [l for l in texte.splitlines() if l.strip() and not l.lstrip().startswith('#')]
    if not lignes:
        return []
    entete = lignes[0]
    delim = ';' if entete.count(';') >= entete.count(',') else ','
    lecteur = csv.reader(io.StringIO('\n'.join(lignes)), delimiter=delim)
    rows = list(lecteur)
    cols = [norm(c).replace(' ', '_') for c in rows[0]]
    attendu = ['cible', 'repere', 'action', 'champ', 'nouvelle_valeur']
    if cols[:5] != attendu:
        raise ValueError("L'en-tête doit être : cible;repere;action;champ;nouvelle_valeur")
    res = []
    for i, r in enumerate(rows[1:], start=2):
        r = (r + [''] * 5)[:5]
        res.append((i, *[c.strip() for c in r]))
    return res


class Command(BaseCommand):
    help = "Applique les corrections de contenu du fichier apps/core/data/corrections.csv (chaque ligne une seule fois)."

    def add_arguments(self, parser):
        parser.add_argument('--simuler', action='store_true', help="Montre les changements sans rien écrire")
        parser.add_argument('--fichier', default=str(FICHIER))

    def handle(self, *args, **opts):
        sim = opts['simuler']
        chemin = Path(opts['fichier'])
        if not chemin.exists():
            self.stdout.write("Aucun fichier de corrections : rien à faire.")
            return
        try:
            lignes = lire_lignes(chemin.read_text(encoding='utf-8-sig'))
        except Exception as e:  # le déploiement ne doit jamais échouer à cause de ce fichier
            self.stdout.write(self.style.ERROR(f"Fichier de corrections illisible : {e}"))
            return
        # Regroupe les lignes « ajouter » qui décrivent le même nouvel élément
        groupes, ordre = {}, []
        for num, cible, repere, action, champ, valeur in lignes:
            cle = (ALIAS_CIBLES.get(norm(cible), norm(cible)), norm(repere), ACTIONS.get(norm(action), action))
            if cle[2] == 'ajouter':
                groupes.setdefault(cle, []).append((num, champ, valeur, cible, repere, action))
                if len(groupes[cle]) == 1:
                    ordre.append(cle)
            else:
                ordre.append(cle + (num,))
                groupes[cle + (num,)] = [(num, champ, valeur, cible, repere, action)]
        n_ok = n_ignore = n_deja = 0
        for cle in ordre:
            items = groupes[cle]
            empreinte = hashlib.sha256('|'.join(f"{cle[0]}|{cle[1]}|{cle[2]}|{norm(c)}|{v}" for _, c, v, *_ in items).encode()).hexdigest()
            resume = f"{cle[0]} · {items[0][4]} · {cle[2]} · " + ', '.join(c for _, c, *_ in items)[:120]
            if CorrectionAppliquee.objects.filter(empreinte=empreinte).exists():
                n_deja += 1
                continue
            num = items[0][0]
            try:
                with transaction.atomic():
                    msg = self.appliquer(cle[0], cle[2], items, sim)
                    if not sim:
                        CorrectionAppliquee.objects.create(empreinte=empreinte, resume=resume[:300])
                self.stdout.write(f"  ligne {num} : {msg}")
                n_ok += 1
            except Exception as e:
                msg = '; '.join(e.messages) if isinstance(e, ValidationError) else str(e)
                self.stdout.write(self.style.WARNING(f"  ligne {num} IGNORÉE : {msg}"))
                n_ignore += 1
        verbe = "seraient appliquées" if sim else "appliquées"
        self.stdout.write(self.style.SUCCESS(f"Corrections : {n_ok} {verbe}, {n_deja} déjà faites, {n_ignore} ignorées."))

    def appliquer(self, cible, action, items, sim):
        if cible not in CIBLES:
            raise ValueError(f"cible inconnue « {cible} » (choisir : {', '.join(CIBLES)})")
        if action not in ('modifier', 'ajouter', 'supprimer'):
            raise ValueError(f"action inconnue « {action} » (modifier, ajouter ou supprimer)")
        modele, champ_repere, champ_filtre, nom = CIBLES[cible]
        repere = items[0][4]
        champs = champs_modifiables(modele)
        # Trouver l'élément visé
        if modele is InfoEtablissement:
            obj = InfoEtablissement.get()
        else:
            texte, _, filtre = repere.partition('@')
            qs = [o for o in modele.objects.all() if norm(getattr(o, champ_repere)) == norm(texte)]
            if cible in ('article', 'filiere') and not qs:
                qs = [o for o in modele.objects.all() if norm(o.slug) == norm(texte)]
            if filtre and champ_filtre:
                qs = [o for o in qs if norm(getattr(o, champ_filtre)) == norm(filtre)]
            if len(qs) > 1:
                raise ValueError(f"plusieurs « {texte} » : préciser avec « {texte} @ zone/emplacement »")
            obj = qs[0] if qs else None
        if action == 'supprimer':
            if obj is None:
                raise ValueError(f"{nom} « {repere} » introuvable")
            if not sim:
                obj.delete()
            return f"{nom} « {repere} » {'serait supprimé' if sim else 'supprimé'}"
        valeurs = {}
        for _, champ, valeur, *_ in items:
            if norm(champ) not in champs:
                raise ValueError(f"champ « {champ} » inconnu pour {nom} (choisir : {', '.join(champs)})")
            f = champs[norm(champ)]
            valeurs[f.name] = convertir(f, valeur)
        if obj is None:
            if action != 'ajouter':
                raise ValueError(f"{nom} « {repere} » introuvable (vérifier l'orthographe du repère, ou utiliser l'action « ajouter »)")
            texte = repere.partition('@')[0].strip()
            if champ_repere and champ_repere not in valeurs:
                valeurs[champ_repere] = texte
            obj = modele(**valeurs)
            obj.full_clean()
            if not sim:
                obj.save()
            return f"{nom} « {repere} » {'serait ajouté' if sim else 'ajouté'}"
        avant = {k: getattr(obj, k) for k in valeurs}
        for k, v in valeurs.items():
            setattr(obj, k, v)
        # On ne valide que les champs modifiés : les autres champs de la fiche ne doivent pas bloquer la correction
        obj.clean_fields(exclude=[f.name for f in modele._meta.get_fields() if getattr(f, 'concrete', False) and f.name not in valeurs])
        if not sim:
            obj.save()
        details = ', '.join(f"{k} : « {str(avant[k])[:40]} » → « {str(v)[:40]} »" for k, v in valeurs.items())
        return f"{nom} « {repere} » : {details}"
