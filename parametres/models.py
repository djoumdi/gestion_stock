from django.db import models
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField

class ParametresMagasin(models.Model):
    """Configuration générale du magasin. Toujours un seul enregistrement
    (pk=1) — utiliser ParametresMagasin.charger() pour y accéder."""

    nom_magasin = models.CharField(max_length=150, default="TechStock")
    adresse = models.CharField(max_length=255, blank=True)
    logo = CloudinaryField('image', folder='parametres', blank=True, null=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    devise = models.CharField(max_length=10, default="FCFA")
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    unite_mesure_defaut = models.CharField(max_length=30, default="unité", blank=True)

    class Meta:
        verbose_name = "Paramètres du magasin"
        verbose_name_plural = "Paramètres du magasin"

    CLE_CACHE = 'parametres_magasin'

    def save(self, *args, **kwargs):
        from django.core.cache import cache
        self.pk = 1  # force le singleton, quel que soit l'appelant
        super().save(*args, **kwargs)
        # Toute modification invalide la copie en cache : la page suivante
        # affiche immédiatement le nouveau nom, le nouveau logo ou la nouvelle TVA.
        cache.delete(self.CLE_CACHE)

    def delete(self, *args, **kwargs):
        raise ValidationError("Les paramètres du magasin ne peuvent pas être supprimés.")

    @classmethod
    def charger(cls):
        from django.core.cache import cache
        objet = cache.get(cls.CLE_CACHE)
        if objet is None:
            objet, _ = cls.objects.get_or_create(pk=1)
            try:
                cache.set(cls.CLE_CACHE, objet, 3600)
            except Exception:
                # Objet non sérialisable par le backend de cache : on continue
                # sans cache plutôt que de faire planter la page.
                pass
        return objet

    def __str__(self):
        return self.nom_magasin
