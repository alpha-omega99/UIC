from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views

app_name = 'portail'
urlpatterns = [
    path('connexion/', views.Connexion.as_view(), name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('tableau-de-bord/', views.tableau_de_bord, name='tableau_de_bord'),
    path('resultats/', views.resultats, name='resultats'),
    path('cartes-admission/', views.cartes, name='cartes'),
    path('certificats/', views.certificats, name='certificats'),
    path('document/<str:type_doc>/<int:pk>/', views.telecharger, name='telecharger'),
    path('mot-de-passe/', views.ChangerMotDePasse.as_view(), name='mot_de_passe'),
    # Réinitialisation par e-mail
    path('mot-de-passe-oublie/', views.ReinitMotDePasse.as_view(), name='reset'),
    path('mot-de-passe-oublie/envoye/', auth_views.PasswordResetDoneView.as_view(template_name='registration/reset_envoye.html'), name='reset_envoye'),
    path('reinitialiser/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/reset_confirm.html', success_url=reverse_lazy('portail:reset_termine')), name='reset_confirm'),
    path('reinitialiser/termine/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/reset_termine.html'), name='reset_termine'),
]
