from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EtudiantAuthForm(AuthenticationForm):
    """Seuls les comptes ayant un profil étudiant actif peuvent entrer.
    Message d'erreur identique dans tous les cas → pas d'énumération de comptes."""
    username = forms.CharField(label='Identifiant (matricule)', max_length=150,
                               widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'username', 'placeholder': 'Votre matricule'}))
    password = forms.CharField(label='Mot de passe', strip=False,
                               widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'placeholder': '••••••••'}))

    def confirm_login_allowed(self, user):
        if not user.is_active or not hasattr(user, 'profil_etudiant'):
            raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login',
                                        params={'username': self.username_field.verbose_name})
