from django.shortcuts import render
from .models import Professeur


def liste(request):
    return render(request, 'professeurs/liste.html', {'professeurs': Professeur.objects.filter(actif=True)})
