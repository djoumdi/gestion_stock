from django.contrib import admin
from .models import Categorie, Marque, Produit, MouvementStock


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom']


@admin.register(Marque)
class MarqueAdmin(admin.ModelAdmin):
    list_display = ['nom']


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'image', 'marque', 'fournisseur', 'categorie', 'prix_achat', 'prix_vente', 'quantite_stock', 'en_alerte']
    list_filter = ['categorie', 'marque', 'fournisseur']
    search_fields = ['nom', 'marque__nom']


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ['produit', 'type_mouvement', 'quantite', 'date']
    list_filter = ['type_mouvement']
