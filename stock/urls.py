from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('', views.liste_produits, name='liste_produits'),
    path('ajouter/', views.ajouter_produit, name='ajouter_produit'),
    path('<int:pk>/', views.detail_produit, name='detail_produit'),
    path('categories-marques/', views.categories_marques, name='categories_marques'),
]
