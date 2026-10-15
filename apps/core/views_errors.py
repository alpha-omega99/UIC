from django.shortcuts import render


def erreur_403(request, exception=None):
    return render(request, '403.html', status=403)


def erreur_404(request, exception=None):
    return render(request, '404.html', status=404)
