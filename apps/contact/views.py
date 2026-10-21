from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django_ratelimit.decorators import ratelimit
from apps.core.notify import notifier
from apps.core.utils import client_ip
from .forms import ContactForm


@ratelimit(key=client_ip, rate='6/h', method='POST', block=True)
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            m = form.save()
            notifier(
                f'[UIC Contact] {m.get_sujet_display()} — {m.prenom} {m.nom}',
                f"Nouveau message reçu via le formulaire de contact.\n\nDe : {m.prenom} {m.nom} <{m.email}>\n"
                f"Téléphone : {m.telephone or '—'}\nSujet : {m.get_sujet_display()}\n\nMessage :\n{m.message}",
                reply_to=m.email)
            messages.success(request, 'Message envoyé ! Nous vous répondons sous 24h.')
            return redirect('contact:contact')
        messages.error(request, 'Veuillez corriger les champs signalés.')
    else:
        form = ContactForm()
    from apps.core.models import FAQ
    return render(request, 'contact/contact.html', {'form': form, 'faqs': FAQ.objects.filter(actif=True)[:3]})
