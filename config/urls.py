from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = 'UIC — Administration'
admin.site.site_title = 'UIC Admin'
admin.site.index_title = 'Gestion du site'

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('apps.core.urls')),
    path('filieres/', include('apps.filieres.urls')),
    path('actualites/', include('apps.actualites.urls')),
    path('admission/', include('apps.admissions.urls')),
    path('galerie/', include('apps.galerie.urls')),
    path('enseignants/', include('apps.professeurs.urls')),
    path('contact/', include('apps.contact.urls')),
    # Images publiques uniquement (MEDIA_ROOT). Aucun document privé n'est servi par le site.
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

handler403 = 'apps.core.views_errors.erreur_403'
handler404 = 'apps.core.views_errors.erreur_404'
