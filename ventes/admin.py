from django.contrib import admin
from .models import Vente, LigneVente, Facture, Paiement


class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 1


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'vendeur', 'date_vente', 'total']
    inlines = [LigneVenteInline]


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ['numero', 'vente', 'date_emission', 'est_payee']
    search_fields = ['numero']


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['facture', 'montant', 'mode_paiement', 'date_paiement']
    list_filter = ['mode_paiement']
