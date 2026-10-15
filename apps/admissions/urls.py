from django.urls import path
from . import views

app_name = 'admissions'
urlpatterns = [
    path('', views.formulaire, name='formulaire'),
    path('merci/', views.merci, name='merci'),
    path('suivi/', views.suivi, name='suivi'),
]
