from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('', views.liste_produits, name='liste_produits'),
    path('ajouter/', views.ajouter_produit, name='ajouter_produit'),
    path('categories-marques/', views.categories_marques, name='categories_marques'),
    path('inventaires/', views.liste_inventaires, name='liste_inventaires'),
    path('inventaires/nouveau/', views.nouvel_inventaire, name='nouvel_inventaire'),
    path('inventaires/<int:pk>/', views.detail_inventaire, name='detail_inventaire'),
    path('mouvements/', views.historique_mouvements, name='historique_mouvements'),
    path('<int:pk>/', views.detail_produit, name='detail_produit'),
    path('<int:pk>/supprimer/', views.supprimer_produit, name='supprimer_produit'),
]
