from django.db import models
from django.core.exceptions import ValidationError


class ParametresMagasin(models.Model):
    """Configuration générale du magasin. Toujours un seul enregistrement
    (pk=1) — utiliser ParametresMagasin.charger() pour y accéder."""

    nom_magasin = models.CharField(max_length=150, default="TechStock")
    logo = models.ImageField(upload_to='parametres/', blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    devise = models.CharField(max_length=10, default="FCFA")
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    unite_mesure_defaut = models.CharField(max_length=30, default="unité", blank=True)

    class Meta:
        verbose_name = "Paramètres du magasin"
        verbose_name_plural = "Paramètres du magasin"

    def save(self, *args, **kwargs):
        self.pk = 1  # force le singleton, quel que soit l'appelant
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Les paramètres du magasin ne peuvent pas être supprimés.")

    @classmethod
    def charger(cls):
        objet, _ = cls.objects.get_or_create(pk=1)
        return objet

    def __str__(self):
        return self.nom_magasin
