from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django_ratelimit.decorators import ratelimit
from apps.core.utils import client_ip
from .forms import ContactForm


@ratelimit(key=client_ip, rate='6/h', method='POST', block=True)
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            m = form.save()
            EmailMessage(
                subject=' '.join(f'[UIC Contact] {m.get_sujet_display()} — {m.prenom} {m.nom}'.split()),
                body=f"De : {m.prenom} {m.nom} <{m.email}>\nTéléphone : {m.telephone or '—'}\n\n{m.message}",
                from_email=settings.DEFAULT_FROM_EMAIL, to=[settings.NOTIFY_EMAIL], reply_to=[m.email],
            ).send(fail_silently=True)
            messages.success(request, 'Message envoyé ! Nous vous répondons sous 24h.')
            return redirect('contact:contact')
        messages.error(request, 'Veuillez corriger les champs signalés.')
    else:
        form = ContactForm()
    from apps.core.models import FAQ
    return render(request, 'contact/contact.html', {'form': form, 'faqs': FAQ.objects.filter(actif=True)[:3]})
