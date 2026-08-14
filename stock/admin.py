from django.contrib import admin
from .models import Categorie, Marque, Produit, MouvementStock, Inventaire, LigneInventaire


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
    # quantite_stock ne doit jamais être modifiée à la main : seuls les
    # MouvementStock (achats, ventes, ajustements d'inventaire) la font varier.
    readonly_fields = ['quantite_stock']


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ['produit', 'type_mouvement', 'quantite', 'date']
    list_filter = ['type_mouvement']


class LigneInventaireInline(admin.TabularInline):
    model = LigneInventaire
    extra = 0


@admin.register(Inventaire)
class InventaireAdmin(admin.ModelAdmin):
    list_display = ['code', 'cree_par', 'statut', 'date_creation', 'date_validation']
    list_filter = ['statut']
    inlines = [LigneInventaireInline]
