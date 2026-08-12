from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.liste_clients, name='liste_clients'),
    path('ajouter/', views.ajouter_client, name='ajouter_client'),
    path('<int:pk>/', views.detail_client, name='detail_client'),
]
