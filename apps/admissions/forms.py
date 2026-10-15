from django import forms
from django.core.exceptions import ValidationError
from apps.filieres.models import Filiere
from .models import DemandeAdmission


class DemandeAdmissionForm(forms.ModelForm):
    site_web = forms.CharField(required=False, label='', widget=forms.TextInput(
        attrs={'tabindex': '-1', 'autocomplete': 'off', 'aria-hidden': 'true'}))   # honeypot (masqué en CSS)

    class Meta:
        model = DemandeAdmission
        fields = ['prenom', 'nom', 'email', 'telephone', 'filiere', 'niveau_entree']
        widgets = {
            'prenom': forms.TextInput(attrs={'id': 'fPrenom', 'placeholder': 'Votre prénom', 'maxlength': 80, 'autocomplete': 'given-name'}),
            'nom': forms.TextInput(attrs={'id': 'fNom', 'placeholder': 'Votre nom', 'maxlength': 80, 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'id': 'fEmail', 'placeholder': 'votre@email.com', 'autocomplete': 'email'}),
            'telephone': forms.TextInput(attrs={'id': 'fTel', 'placeholder': '(+225) 00 00 00 00 00', 'type': 'tel', 'autocomplete': 'tel'}),
            'filiere': forms.Select(attrs={'id': 'fFiliere'}),
            'niveau_entree': forms.Select(attrs={'id': 'fNiveau'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['filiere'].queryset = Filiere.objects.filter(actif=True)
        self.fields['filiere'].empty_label = 'Sélectionnez une filière'
        self.fields['niveau_entree'].choices = [('', 'Choisissez un niveau')] + list(self.fields['niveau_entree'].choices)[1:]

    def clean_site_web(self):
        if self.cleaned_data.get('site_web'):
            raise ValidationError('Erreur.')
        return ''

    def clean_email(self):
        return self.cleaned_data['email'].lower().strip()


class SuiviForm(forms.Form):
    email = forms.EmailField(max_length=254)
    numero = forms.CharField(max_length=20)

    def clean_numero(self):
        return self.cleaned_data['numero'].strip().upper()

    def clean_email(self):
        return self.cleaned_data['email'].lower().strip()
