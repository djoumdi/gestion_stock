# api/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views
from .clients import ClientListView
from .ventes import VenteViewSet

routeur = DefaultRouter()
routeur.register('produits', views.ProduitViewSet, basename='produit')
routeur.register('ventes', VenteViewSet, basename='vente')

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtenir'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_rafraichir'),
    path('auth/moi/', views.MoiView.as_view(), name='moi'),
    path('categories/', views.CategorieListView.as_view(), name='categories'),
    path('clients/', ClientListView.as_view(), name='clients'),
    path('', include(routeur.urls)),
]
