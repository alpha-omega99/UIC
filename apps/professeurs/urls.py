from django.urls import path
from . import views

app_name = 'professeurs'
urlpatterns = [path('', views.liste, name='liste')]
