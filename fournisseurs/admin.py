from django.contrib import admin
from .models import Fournisseur


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'telephone', 'email', 'ville', 'actif']
    list_filter = ['actif', 'ville']
    search_fields = ['nom']
