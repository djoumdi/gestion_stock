from django.contrib import admin
from .models import Achat, LigneAchat


class LigneAchatInline(admin.TabularInline):
    model = LigneAchat
    extra = 1


@admin.register(Achat)
class AchatAdmin(admin.ModelAdmin):
    list_display = ['code', 'fournisseur', 'cree_par', 'statut', 'date_achat', 'total']
    list_filter = ['statut']
    inlines = [LigneAchatInline]
