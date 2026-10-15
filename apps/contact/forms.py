from django import forms
from django.core.exceptions import ValidationError
from .models import MessageContact


class ContactForm(forms.ModelForm):
    site_web = forms.CharField(required=False, label='', widget=forms.TextInput(
        attrs={'tabindex': '-1', 'autocomplete': 'off', 'aria-hidden': 'true'}))   # honeypot

    class Meta:
        model = MessageContact
        fields = ['prenom', 'nom', 'email', 'telephone', 'sujet', 'message']
        widgets = {
            'prenom': forms.TextInput(attrs={'placeholder': 'Votre prénom', 'maxlength': 80}),
            'nom': forms.TextInput(attrs={'placeholder': 'Votre nom', 'maxlength': 80}),
            'email': forms.EmailInput(attrs={'placeholder': 'votre@email.com'}),
            'telephone': forms.TextInput(attrs={'placeholder': '(+225) 00 00 00 00 00', 'type': 'tel'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Votre message...', 'maxlength': 2000}),
        }

    def clean_site_web(self):
        if self.cleaned_data.get('site_web'):
            raise ValidationError('Erreur.')
        return ''

    def clean_email(self):
        return self.cleaned_data['email'].lower().strip()
