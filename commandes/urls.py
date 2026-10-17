from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'commandes'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='commandes:catalogue', permanent=False), name='accueil'),
    # Portail client
    path('inscription/', views.inscription, name='inscription'),
    path('catalogue/', views.catalogue, name='catalogue'),
    path('commander/', views.passer_commande, name='passer_commande'),
    path('mes-commandes/', views.mes_commandes, name='mes_commandes'),
    path('mes-commandes/<int:pk>/', views.detail_commande, name='detail_commande'),

    # Gestion staff
    path('gestion/', views.liste_commandes_client, name='liste_commandes_client'),
    path('gestion/<int:pk>/', views.staff_detail_commande, name='staff_detail_commande'),

    # Espace livreur
    path('livraisons/', views.mes_livraisons, name='mes_livraisons'),
    path('livraisons/<int:pk>/statut/', views.changer_statut_livraison, name='changer_statut_livraison'),
]
