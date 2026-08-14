# accounts/models.py
from django.db import models
from django.conf import settings


class Notification(models.Model):
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    lien = models.CharField(max_length=255, blank=True)
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return self.message


class HistoriqueAction(models.Model):
    """Journal d'audit : trace qui a fait quoi et quand sur les actions clés du système."""
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_historique')
    action = models.CharField(max_length=255)
    lien = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Action de l'historique"
        verbose_name_plural = "Historique des actions"

    def __str__(self):
        auteur = self.utilisateur or "Utilisateur supprimé"
        return f"{auteur} — {self.action}"
