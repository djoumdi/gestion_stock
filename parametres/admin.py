from django.contrib import admin
from .models import ParametresMagasin


@admin.register(ParametresMagasin)
class ParametresMagasinAdmin(admin.ModelAdmin):
    list_display = ('nom_magasin', 'devise', 'taux_tva')

    def has_add_permission(self, request):
        # Singleton : jamais plus d'un enregistrement
        return not ParametresMagasin.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
