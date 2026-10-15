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
        urls = ['/', '/a-propos/', '/faq/', '/filieres/', '/actualites/', '/galerie/', '/enseignants/', '/contact/',
                '/admission/', '/admission/suivi/', '/portail/connexion/', '/portail/mot-de-passe-oublie/']
        urls += [f.get_absolute_url() for f in Filiere.objects.all()]
        from apps.actualites.models import Article
        urls += [a.get_absolute_url() for a in Article.objects.all()]
        for u in urls:
            r = self.client.get(u)
            self.assertEqual(r.status_code, 200, u)

    def test_accueil_contient_le_contenu_de_la_maquette(self):
        html = self.client.get('/').content.decode()
        for txt in ['font bouger', 'Gestion &amp; Management', "Filières d'excellence", 'Commencez votre candidature',
                    'Konan Stéphane', 'Vie du campus', "L'UIC, un cadre d'excellence", 'Mot du Président']:
            self.assertIn(txt, html)
        self.assertEqual(html.count('class="fil-card reveal"'), 6)

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
        for secret in ('Awa', 'Traoré', 'En attente', self.filiere.nom):
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
