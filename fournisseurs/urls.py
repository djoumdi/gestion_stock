from django.urls import path
from . import views

app_name = 'fournisseurs'

urlpatterns = [
    path('', views.liste_fournisseurs, name='liste_fournisseurs'),
    path('ajouter/', views.ajouter_fournisseur, name='ajouter_fournisseur'),
    path('<int:pk>/', views.detail_fournisseur, name='detail_fournisseur'),
]
