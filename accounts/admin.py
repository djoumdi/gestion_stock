from django.contrib import admin
from .models import HistoriqueAction


@admin.register(HistoriqueAction)
class HistoriqueActionAdmin(admin.ModelAdmin):
    list_display = ('date', 'utilisateur', 'action')
    list_filter = ('utilisateur',)
    search_fields = ('action', 'utilisateur__username')
    ordering = ('-date',)
