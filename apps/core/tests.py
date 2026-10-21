"""Tests fonctionnels + sécurité.  Lancer :  python manage.py test"""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.admissions.models import DemandeAdmission
from apps.filieres.models import Filiere
from apps.portail.models import CarteAdmission, Certificat, ProfilEtudiant, Resultat

User = get_user_model()
PWD = 'Sup3r-Secret-Passw0rd!'


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_uic', stdout=StringIO())
        cls.filiere = Filiere.objects.first()
        cls.u1 = User.objects.create_user('E001', 'a@x.com', PWD, first_name='Awa')
        cls.u2 = User.objects.create_user('E002', 'b@x.com', PWD, first_name='Koffi')
        cls.p1 = ProfilEtudiant.objects.create(user=cls.u1, matricule='E001', filiere=cls.filiere, annee_inscription=2024)
        cls.p2 = ProfilEtudiant.objects.create(user=cls.u2, matricule='E002', filiere=cls.filiere, annee_inscription=2024)
        cls.staff = User.objects.create_user('staff', 's@x.com', PWD, is_staff=True)  # personnel SANS profil étudiant

    def setUp(self):
        cache.clear()


class PagesPubliques(Base):
    def test_toutes_les_pages_repondent(self):
        urls = ['/', '/a-propos/', '/faq/', '/filieres/', '/actualites/', '/enseignants/', '/contact/',
                '/admission/', '/admission/suivi/', '/portail/connexion/', '/portail/mot-de-passe-oublie/']
        urls += [f.get_absolute_url() for f in Filiere.objects.all()]
        from apps.actualites.models import Article
        urls += [a.get_absolute_url() for a in Article.objects.all()]
        for u in urls:
            r = self.client.get(u)
            self.assertEqual(r.status_code, 200, u)

    def test_accueil_contient_le_contenu_de_la_maquette(self):
        html = self.client.get('/').content.decode()
        for txt in ['font bouger', 'BTS Gestion Commerciale (GEC)', "Filières d'excellence", 'Rejoignez la prochaine promotion',
                    'À la une', "L'UIC, un cadre d'excellence", 'Mot du Président']:
            self.assertIn(txt, html)
        self.assertIn('class="cycle-card"', html)
        self.assertNotIn('alumni', html)

    def test_404_personnalise_et_admin_par_defaut_cache(self):
        self.assertEqual(self.client.get('/inexistant/').status_code, 404)
        self.assertEqual(self.client.get('/admin/').status_code, 404)           # l'URL admin standard n'existe pas
        self.assertEqual(self.client.get('/gestion-uic/login/').status_code, 200)

    def test_filiere_non_publiee_introuvable(self):
        Filiere.objects.filter(pk=self.filiere.pk).update(actif=False)
        self.assertEqual(self.client.get(self.filiere.get_absolute_url()).status_code, 404)


class EnTetesSecurite(Base):
    def test_csp_et_en_tetes(self):
        r = self.client.get('/')
        csp = r.headers.get('Content-Security-Policy', '')
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertEqual(r.headers['X-Frame-Options'], 'DENY')
        self.assertEqual(r.headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn('Permissions-Policy', r.headers)

    def test_aucun_script_inline_dans_les_pages(self):
        import re
        for u in ['/', '/contact/', '/admission/', '/portail/connexion/']:
            html = self.client.get(u).content.decode()
            for m in re.finditer(r'<script([^>]*)>', html):
                self.assertIn('src=', m.group(1), f'script inline sur {u}')
            self.assertNotRegex(html, r'\son(click|load|error|submit)=', u)


class Admission(Base):
    DATA = dict(prenom='Awa', nom='Traoré', email='AWA@Example.com', telephone='+225 07 00 00 00 00', niveau_entree='bac-l1')

    def post(self, **over):
        d = {**self.DATA, 'filiere': self.filiere.pk, **over}
        return self.client.post('/admission/', d)

    def test_candidature_valide(self):
        r = self.post()
        self.assertRedirects(r, '/admission/merci/')
        d = DemandeAdmission.objects.get()
        self.assertEqual(d.email, 'awa@example.com')
        self.assertRegex(d.numero_dossier, r'^UIC-\d{4}-[0-9A-F]{6}$')          # numéro non séquentiel
        self.assertContains(self.client.get('/admission/merci/'), d.numero_dossier)

    def test_merci_inaccessible_sans_soumission(self):
        self.assertRedirects(self.client.get('/admission/merci/'), '/admission/')

    def test_invalides_refuses(self):
        for over in (dict(email='pas-un-email'), dict(telephone='<script>'), dict(filiere=99999), dict(niveau_entree='x'), dict(prenom='')):
            self.assertEqual(self.post(**over).status_code, 200)
        self.assertEqual(DemandeAdmission.objects.count(), 0)

    def test_honeypot(self):
        self.assertEqual(self.post(site_web='http://spam').status_code, 200)
        self.assertEqual(DemandeAdmission.objects.count(), 0)

    def test_xss_echappe(self):
        self.post(prenom='<script>alert(1)</script>')
        d = DemandeAdmission.objects.get()
        d.statut = 'accepte'; d.save()
        r = self.client.post('/admission/suivi/', {'email': d.email, 'numero': d.numero_dossier})
        self.assertNotIn('<script>alert(1)</script>', r.content.decode())

    def test_csrf_obligatoire(self):
        c = Client(enforce_csrf_checks=True)
        self.assertEqual(c.post('/admission/', {**self.DATA, 'filiere': self.filiere.pk}).status_code, 403)
        self.assertEqual(c.post('/contact/', {}).status_code, 403)

    def test_limitation_de_debit(self):
        for _ in range(6):
            self.post(prenom='')
        self.assertEqual(self.post(prenom='').status_code, 403)

    def test_suivi_sans_enumeration(self):
        self.post()
        d = DemandeAdmission.objects.get()
        ok = self.client.post('/admission/suivi/', {'email': d.email, 'numero': d.numero_dossier})
        self.assertContains(ok, d.numero_dossier)
        bad = self.client.post('/admission/suivi/', {'email': 'autre@x.com', 'numero': d.numero_dossier})
        self.assertContains(bad, 'Aucun dossier ne correspond')                   # mauvais e-mail : rien n'est révélé
        for secret in ('Awa', 'Traoré', 'En attente', Filiere.objects.order_by('-ordre').first().nom):
            self.assertNotContains(bad, secret)


class Contact(Base):
    def test_envoi(self):
        from django.core import mail
        r = self.client.post('/contact/', dict(prenom='A', nom='B', email='a@b.com', sujet='autre', message='Bonjour'))
        self.assertRedirects(r, '/contact/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].reply_to, ['a@b.com'])

    def test_injection_entete(self):
        from django.core import mail
        self.client.post('/contact/', dict(prenom='A\r\nBcc: x@evil.com', nom='B', email='a@b.com', sujet='autre', message='m'))
        for m in mail.outbox:
            self.assertNotIn('\n', m.subject)
            self.assertNotIn('x@evil.com', ''.join(m.bcc))


class Portail(Base):
    def login(self, u='E001'):
        self.assertTrue(self.client.login(username=u, password=PWD))

    def test_pages_privees_exigent_connexion(self):
        for u in ['/portail/tableau-de-bord/', '/portail/resultats/', '/portail/cartes-admission/', '/portail/certificats/',
                  '/portail/document/carte/1/', '/portail/mot-de-passe/']:
            r = self.client.get(u)
            self.assertEqual(r.status_code, 302, u)
            self.assertIn('/portail/connexion/', r['Location'])

    def test_connexion_et_message_generique(self):
        bad_user = self.client.post('/portail/connexion/', {'username': 'inconnu', 'password': 'x'})
        bad_pwd = self.client.post('/portail/connexion/', {'username': 'E001', 'password': 'x'})
        self.assertEqual(bad_user.context['form'].non_field_errors(), bad_pwd.context['form'].non_field_errors())
        ok = self.client.post('/portail/connexion/', {'username': 'E001', 'password': PWD})
        self.assertRedirects(ok, '/portail/tableau-de-bord/')

    def test_personnel_sans_profil_ne_peut_pas_entrer(self):
        r = self.client.post('/portail/connexion/', {'username': 'staff', 'password': PWD})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_open_redirect_bloque(self):
        for nxt in ('https://evil.com', '//evil.com', 'javascript:alert(1)'):
            r = self.client.post('/portail/connexion/?next=' + nxt, {'username': 'E001', 'password': PWD, 'next': nxt})
            self.assertNotIn('evil', r['Location'], nxt)
            self.client.logout()

    def test_brute_force_bloque(self):
        for _ in range(6):
            self.client.post('/portail/connexion/', {'username': 'E001', 'password': 'faux'})
        r = self.client.post('/portail/connexion/', {'username': 'E001', 'password': PWD})   # même le bon mot de passe est refusé
        self.assertEqual(r.status_code, 403)

    def test_deconnexion_post_uniquement(self):
        self.login()
        self.assertEqual(self.client.get('/portail/deconnexion/').status_code, 405)
        self.assertEqual(self.client.post('/portail/deconnexion/').status_code, 302)
        self.assertEqual(self.client.get('/portail/tableau-de-bord/').status_code, 302)

    def test_isolation_des_resultats(self):
        Resultat.objects.create(etudiant=self.p1, matiere='SECRET-DE-AWA', note=15, semestre=1, annee_academique='2025-2026', publie=True)
        Resultat.objects.create(etudiant=self.p1, matiere='BROUILLON-NON-PUBLIE', note=3, semestre=1, annee_academique='2025-2026', publie=False)
        self.login('E002')
        html = self.client.get('/portail/resultats/').content.decode()
        self.assertNotIn('SECRET-DE-AWA', html)
        self.client.logout(); self.login('E001')
        html = self.client.get('/portail/resultats/').content.decode()
        self.assertIn('SECRET-DE-AWA', html)
        self.assertNotIn('BROUILLON-NON-PUBLIE', html)

    def test_telechargement_prive(self):
        carte = CarteAdmission.objects.create(etudiant=self.p1, titre='Examens S1', annee_academique='2025-2026', publie=True,
                                              fichier=SimpleUploadedFile('carte.pdf', b'%PDF-1.4 test'))
        cert = Certificat.objects.create(etudiant=self.p1, type_document='scolarite', annee_academique='2025-2026', publie=False,
                                         fichier=SimpleUploadedFile('c.pdf', b'%PDF-1.4 test'))
        self.addCleanup(carte.fichier.delete, False); self.addCleanup(cert.fichier.delete, False)
        url = f'/portail/document/carte/{carte.pk}/'
        # anonyme → connexion ; autre étudiant → 404 ; propriétaire → fichier ; non publié → 404
        self.assertEqual(self.client.get(url).status_code, 302)
        self.login('E002'); self.assertEqual(self.client.get(url).status_code, 404)
        self.client.logout(); self.login('E001')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(b''.join(r.streaming_content), b'%PDF-1.4 test')
        self.assertEqual(r['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(self.client.get(f'/portail/document/certificat/{cert.pk}/').status_code, 404)
        self.assertEqual(self.client.get('/portail/document/autre/1/').status_code, 404)

    def test_fichiers_prives_jamais_servis_par_media(self):
        carte = CarteAdmission.objects.create(etudiant=self.p1, titre='x', annee_academique='2025-2026', publie=True,
                                              fichier=SimpleUploadedFile('carte.pdf', b'x'))
        self.addCleanup(carte.fichier.delete, False)
        self.assertEqual(self.client.get('/media/' + carte.fichier.name).status_code, 404)

    def test_mention(self):
        r = Resultat(etudiant=self.p1, matiere='m', note=14, note_max=20, semestre=1, annee_academique='2025-2026')
        self.assertEqual(r.mention, 'Bien')


class Config(TestCase):
    def test_secret_key_et_debug(self):
        from django.conf import settings
        self.assertGreater(len(settings.SECRET_KEY), 30)


class FilieresExtensibles(Base):
    """Le catalogue doit rester propre quand de nouvelles formations sont ajoutées."""

    def _ajouter(self, nb, niveau='BTS', en_avant=True):
        from apps.filieres.models import NiveauFormation
        niv, _ = NiveauFormation.objects.get_or_create(nom=niveau)
        for i in range(nb):
            f = Filiere.objects.create(nom=f"{niveau} Test {i}", resume="Résumé", description="Description", duree="2 ans",
                                       niveau_requis="Bac", en_avant=en_avant, ordre=100 + i)
            f.niveaux.add(niv)

    def test_filtre_genere_depuis_la_base(self):
        html = self.client.get('/filieres/').content.decode()
        from apps.filieres.models import NiveauFormation
        self.assertIn('data-f="bts"', html)
        NiveauFormation.objects.create(nom='Doctorat')
        self.assertNotIn('data-f="doctorat"', self.client.get('/filieres/').content.decode())   # niveau vide : pas de filtre
        self._ajouter(1, 'Doctorat')
        self.assertIn('data-f="doctorat"', self.client.get('/filieres/').content.decode())

    def test_page_filieres_liste_tout_et_accueil_limite(self):
        self._ajouter(10, 'BTS')
        self.assertEqual(self.client.get('/filieres/').content.decode().count('class="ccard"'), 29)
        accueil = self.client.get('/').content.decode()
        self.assertIn('class="cycle-card"', accueil)
        self.assertIn('Voir toutes les formations (29)', accueil)

    def test_accueil_montre_un_bloc_par_cycle_present(self):
        Filiere.objects.update(actif=False)
        self._ajouter(1, 'Master', en_avant=True)
        self.assertEqual(self.client.get('/').content.decode().count('class="cycle-card"'), 1)
        self.assertEqual(self.client.get('/filieres/').content.decode().count('class="ccard"'), 1)

    def test_detail_propose_dautres_formations(self):
        html = self.client.get(self.filiere.get_absolute_url()).content.decode()
        self.assertIn('Autres formations', html)
        self.assertEqual(html.count('class="fcard"'), 3)
        self.assertNotIn(f'href="{self.filiere.get_absolute_url()}" data-lv', html)   # pas elle-même

    def test_filiere_sans_niveau_ne_casse_rien(self):
        Filiere.objects.create(nom="Sans niveau", resume="r", description="d", duree="1 an", niveau_requis="Bac")
        for u in ('/', '/filieres/', '/filieres/sans-niveau/'):
            self.assertEqual(self.client.get(u).status_code, 200)


class CatalogueParEcole(TestCase):
    def test_groupes_et_filtres(self):
        from apps.filieres.models import Filiere, Pole
        droit = Pole.objects.create(nom="École de Droit")
        Filiere.objects.create(nom="Droit privé", resume="r", description="d", duree="3 ans", niveau_requis="Bac", pole=droit)
        Filiere.objects.create(nom="Sans école", resume="r", description="d", duree="2 ans", niveau_requis="Bac")
        html = self.client.get('/filieres/').content.decode()
        self.assertIn('École de Droit', html)
        self.assertEqual(html.count('class="ccard"'), 2)
        self.assertIn('Autres formations', html)

    def test_sans_ecole_pas_de_titre_de_groupe(self):
        from apps.filieres.models import Filiere
        Filiere.objects.create(nom="Seule", resume="r", description="d", duree="2 ans", niveau_requis="Bac")
        html = self.client.get('/filieres/').content.decode()
        self.assertNotIn('Autres formations', html)
        self.assertEqual(html.count('class="ccard"'), 1)


class PagesLegales(TestCase):
    URLS = ['/mentions-legales/', '/confidentialite/', '/conditions-utilisation/']

    def test_pages_accessibles_et_liees_dans_le_pied_de_page(self):
        for u in self.URLS:
            self.assertEqual(self.client.get(u).status_code, 200, u)
        accueil = self.client.get('/').content.decode()
        for u in self.URLS:
            self.assertIn(f'href="{u}"', accueil)

    def test_mentions_masquent_les_champs_vides_et_affichent_les_remplis(self):
        from apps.core.models import InfoEtablissement
        html = self.client.get('/mentions-legales/').content.decode()
        self.assertNotIn('RCCM', html.split('Hébergement')[0])
        info = InfoEtablissement.get(); info.rccm = 'CI-ABJ-2004-B-1234'; info.directeur_publication = 'Dr X'; info.save()
        html = self.client.get('/mentions-legales/').content.decode()
        self.assertIn('CI-ABJ-2004-B-1234', html); self.assertIn('Dr X', html)

    def test_formulaires_renvoient_vers_la_confidentialite(self):
        for u in ('/contact/', '/'):
            self.assertIn('/confidentialite/', self.client.get(u).content.decode())

    def test_temoignages_supprimes(self):
        self.assertNotIn('alumni', self.client.get('/').content.decode())


class GalerieCarrousel(TestCase):
    @classmethod
    def setUpTestData(cls):
        from apps.galerie.models import Album, Photo
        for n in ('Alpha', 'Beta'):
            a = Album.objects.create(titre=f"Album {n}")
            for i in range(3):
                Photo.objects.create(album=a, image_statique=f"img/campus/vie-etudiante-0{i+1}.webp", legende=f"Légende {n} {i}", ordre=i)

    def test_page_galerie_une_section_par_album_avec_carrousel(self):
        html = self.client.get('/actualites/').content.decode()
        self.assertEqual(html.count('class="gal-section"'), 2)
        self.assertEqual(html.count('class="gal-open"'), 6)
        self.assertIn('data-gal="album-alpha"', html)
        self.assertIn('data-cap="Légende Beta 1"', html)

    def test_detail_album_images_agrandissables(self):
        html = self.client.get('/galerie/album-alpha/').content.decode()
        self.assertEqual(html.count('class="gal-open"'), 3)

    def test_accueil_section_vie_du_campus(self):
        html = self.client.get('/').content.decode()
        self.assertIn('id="vie-du-campus"', html)
        self.assertEqual(html.count('class="gal-open"'), 6)

    def test_accueil_sans_photos_pas_de_section(self):
        from apps.galerie.models import Album
        Album.objects.all().delete()
        self.assertNotIn('vie-du-campus', self.client.get('/').content.decode())


class SeedProduction(TestCase):
    """Le site réel ne contient aucune donnée de démonstration non vérifiée."""

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_production')

    def test_seulement_les_formations_reelles(self):
        from apps.actualites.models import Article
        from apps.core.models import FAQ, Chiffre, JalonHistoire, Valeur
        self.assertEqual(Filiere.objects.filter(actif=True).count(), 19)
        self.assertEqual(Article.objects.count(), 0)
        for m in (Chiffre, Valeur, JalonHistoire, FAQ):
            self.assertEqual(m.objects.count(), 0, m.__name__)

    def test_idempotent_et_respecte_les_modifications(self):
        from django.core.management import call_command
        Filiere.objects.filter(slug='bts-ida').update(duree='Durée modifiée')
        call_command('seed_production')
        self.assertEqual(Filiere.objects.filter(actif=True).count(), 19)
        self.assertTrue(Filiere.objects.filter(duree='Durée modifiée').exists())

    def test_pages_sans_sections_vides_ni_chiffres_inventes(self):
        html = self.client.get('/').content.decode()
        self.assertEqual(self.client.get('/').status_code, 200)
        for absent in ('id="president"', 'class="statsbar"', 'class="chiffres"', 'class="pourquoi"', "20 ans d'excellence"):
            self.assertNotIn(absent, html, absent)
        a = self.client.get('/a-propos/').content.decode()
        for faux in ('45 étudiants', '1 200', 'milliers de réussites'):
            self.assertNotIn(faux, a, faux)
        for u in ('/filieres/', '/actualites/', '/faq/', '/mentions-legales/'):
            self.assertEqual(self.client.get(u).status_code, 200, u)


class CorrectionsContenu(TestCase):
    """Le fichier corrections.csv applique les demandes de l'UIC, une seule fois par ligne."""

    @classmethod
    def setUpTestData(cls):
        from apps.core.models import Chiffre, JalonHistoire
        Chiffre.objects.create(emplacement='section', valeur=1200, suffixe='+', libelle='Étudiants inscrits')
        Chiffre.objects.create(emplacement='barre', valeur=95, suffixe='%', libelle='Taux de réussite')
        Chiffre.objects.create(emplacement='section', valeur=95, suffixe='%', libelle='Taux de réussite')
        JalonHistoire.objects.create(annee='2004', titre='Fondation', texte='Ancien texte')

    def _appliquer(self, contenu, *args):
        import tempfile
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(contenu)
        out = StringIO()
        call_command('appliquer_corrections', '--fichier', f.name, *args, stdout=out)
        return out.getvalue()

    ENTETE = 'cible;repere;action;champ;nouvelle_valeur\n'

    def test_modifier_ajouter_supprimer_et_idempotence(self):
        from apps.core.models import FAQ, Chiffre, InfoEtablissement, JalonHistoire
        csv_ = (self.ENTETE + "chiffre;Étudiants inscrits;modifier;valeur;1 500\n"
                "jalon;2004;modifier;texte;Texte validé\n"
                "info;;modifier;directeur_publication;M. Exemple\n"
                "faq;Nouvelle question ?;ajouter;reponse;La réponse\n")
        out = self._appliquer(csv_)
        self.assertIn('4 appliquées', out)
        self.assertEqual(Chiffre.objects.get(libelle='Étudiants inscrits').valeur, 1500)
        self.assertEqual(JalonHistoire.objects.get(annee='2004').texte, 'Texte validé')
        self.assertEqual(InfoEtablissement.get().directeur_publication, 'M. Exemple')
        self.assertTrue(FAQ.objects.filter(question='Nouvelle question ?').exists())
        # Modification manuelle ensuite dans l'administration : une relance ne l'écrase pas
        Chiffre.objects.filter(libelle='Étudiants inscrits').update(valeur=1600)
        out = self._appliquer(csv_)
        self.assertIn('0 appliquées, 4 déjà faites', out)
        self.assertEqual(Chiffre.objects.get(libelle='Étudiants inscrits').valeur, 1600)

    def test_lignes_invalides_ignorees_sans_bloquer_le_reste(self):
        from apps.core.models import JalonHistoire
        out = self._appliquer(self.ENTETE + "chiffre;Taux de réussite;modifier;valeur;80\n"      # ambigu
                              "info;;modifier;champ_inconnu;x\n"                               # champ inconnu
                              "chiffre;Inexistant;modifier;valeur;3\n"                         # introuvable
                              "jalon;2004;modifier;titre;Fondation officielle\n")
        self.assertIn('1 appliquées', out)
        self.assertIn('3 ignorées', out)
        self.assertEqual(JalonHistoire.objects.get(annee='2004').titre, 'Fondation officielle')

    def test_simulation_ne_modifie_rien(self):
        from apps.core.models import Chiffre
        out = self._appliquer(self.ENTETE + "chiffre;Étudiants inscrits;modifier;valeur;2000\n", '--simuler')
        self.assertIn('seraient appliquées', out)
        self.assertEqual(Chiffre.objects.get(libelle='Étudiants inscrits').valeur, 1200)

    def test_ancre_precise_et_fichier_sans_en_tete_valide(self):
        from apps.core.models import Chiffre
        self._appliquer(self.ENTETE + "chiffre;Taux de réussite @ barre;modifier;valeur;88\n")
        self.assertEqual(Chiffre.objects.get(libelle='Taux de réussite', emplacement='barre').valeur, 88)
        self.assertEqual(Chiffre.objects.get(libelle='Taux de réussite', emplacement='section').valeur, 95)
        out = self._appliquer("a;b;c\n1;2;3\n")
        self.assertIn('illisible', out)


class NotificationsEmail(TestCase):
    """Les formulaires enregistrent en base ET envoient un e-mail complet à NOTIFY_EMAIL."""

    def setUp(self):
        cache.clear()

    def test_contact_envoie_mail_complet_a_plusieurs_destinataires(self):
        from django.core import mail
        with self.settings(NOTIFY_EMAIL='a@uic.ci, b@uic.ci'):
            self.client.post('/contact/', dict(prenom='Awa', nom='Koné', email='awa@x.com', telephone='0102030405',
                                               sujet='autre', message='Bonjour tout le monde'))
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual(m.to, ['a@uic.ci', 'b@uic.ci'])
        self.assertIn('Bonjour tout le monde', m.body)
        self.assertIn('0102030405', m.body)
        self.assertEqual(m.reply_to, ['awa@x.com'])

    def test_echec_envoi_ne_perd_pas_la_soumission(self):
        from unittest import mock
        from apps.contact.models import MessageContact as Message
        with mock.patch('django.core.mail.EmailMessage.send', side_effect=OSError('smtp bloqué')):
            with self.assertLogs('apps.core.notify', level='ERROR'):
                r = self.client.post('/contact/', dict(prenom='A', nom='B', email='a@b.com', sujet='autre', message='m'))
        self.assertRedirects(r, '/contact/')
        self.assertEqual(Message.objects.count(), 1)


class NouvellesFormations(TestCase):
    def setUp(self):
        from django.core.management import call_command
        call_command('charger_nouvelles_formations', stdout=StringIO())

    def test_vingt_formations_et_idempotence(self):
        from django.core.management import call_command
        from apps.filieres.models import Filiere
        self.assertEqual(Filiere.objects.filter(nouveau=True).count(), 20)
        call_command('charger_nouvelles_formations', stdout=StringIO())
        self.assertEqual(Filiere.objects.filter(nouveau=True).count(), 20)

    def test_modification_admin_conservee(self):
        from django.core.management import call_command
        from apps.filieres.models import Filiere
        Filiere.objects.filter(slug='licence-grh').update(frais='Scolarité: 700.000 FCFA')
        call_command('charger_nouvelles_formations', stdout=StringIO())
        self.assertEqual(Filiere.objects.get(slug='licence-grh').frais, 'Scolarité: 700.000 FCFA')

    def test_pages_detail_et_accueil(self):
        r = self.client.get('/filieres/licence-qhse/')
        self.assertContains(r, 'Programme détaillé')
        self.assertContains(r, 'Compétences acquises')
        self.assertContains(r, 'Poursuite d')
        self.assertNotContains(r, '[')
        m = self.client.get('/filieres/master-qhse-rse/')
        self.assertContains(m, 'prolonge la')
        self.assertNotContains(self.client.get('/'), 'Nouvelles licences et masters')

    def test_aucun_placeholder_dans_les_donnees(self):
        from apps.filieres.models import Filiere
        for f in Filiere.objects.filter(nouveau=True):
            for champ in ('frais', 'admission', 'organisation', 'objectif'):
                self.assertNotIn('[', getattr(f, champ), f.slug)
                self.assertNotIn('à compléter', getattr(f, champ), f.slug)


class AccueilCyclesEtOnglets(TestCase):
    def test_accueil_affiche_les_cycles_sans_la_section_nouveautes(self):
        from django.core.management import call_command
        call_command('seed_formations', stdout=StringIO()); call_command('charger_nouvelles_formations', stdout=StringIO())
        html = self.client.get('/').content.decode()
        for t in ('Classes préparatoires', 'BTS', 'Licences', 'Masters', 'Formations continues'):
            self.assertIn(t, html)
        self.assertNotIn('Nouvelles licences et masters', html)
        self.assertIn('?niveau=licence,licence-professionnelle', html)

    def test_galerie_redirige_vers_onglet_et_page_fusionnee(self):
        self.assertRedirects(self.client.get('/galerie/'), '/actualites/#galerie', fetch_redirect_response=False)
        html = self.client.get('/actualites/').content.decode()
        self.assertIn('id="panel-galerie"', html)
        self.assertIn('id="panel-actualites"', html)
