from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('', views.home, name='home'),
    path('a-propos/', views.apropos, name='apropos'),
    path('faq/', views.faq, name='faq'),
]
