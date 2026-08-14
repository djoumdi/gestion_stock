# ventes/models.py
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from stock.models import Produit


class Vente(models.Model):
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, related_name='ventes')
    vendeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventes_effectuees')
    date_vente = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vente #{self.id} - {self.date_vente.strftime('%d/%m/%Y')}"

    @property
    def code(self):
        return f"VTE-{self.pk:06d}" if self.pk else "VTE-EN COURS"

    @property
    def total(self):
        return sum(ligne.sous_total for ligne in self.lignes.all())


class LigneVente(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire

    # Pas de save() qui touche au stock ici : comme pour LigneAchat, le stock est
    # décrémenté explicitement dans la vue (nouvelle_vente) via MouvementStock,
    # pour que chaque vente laisse une trace dans l'historique des mouvements.
    def save(self, *args, **kwargs):
        if not self.prix_unitaire:
            self.prix_unitaire = self.produit.prix_vente
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom}"


class Facture(models.Model):
    vente = models.OneToOneField(Vente, on_delete=models.CASCADE, related_name='facture')
    numero = models.CharField(max_length=30, unique=True, blank=True)
    date_emission = models.DateTimeField(auto_now_add=True)
    # Jeton opaque utilisé pour le lien public envoyé au client (WhatsApp, email...) :
    # on ne veut surtout pas exposer /ventes/<id>/facture/ qui exige une connexion
    # et dont l'id est devinable. Ce token permet une page de consultation publique
    # sans authentification, sans révéler ni l'id interne ni les autres factures.
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.numero:
            self.numero = f"FAC-{self.pk:06d}"
            super().save(update_fields=['numero'])

    def __str__(self):
        return self.numero

    @property
    def total(self):
        return self.vente.total

    @property
    def est_payee(self):
        return hasattr(self, 'paiement')


class Paiement(models.Model):
    ESPECES = 'especes'
    MOBILE_MONEY = 'mobile_money'
    CARTE = 'carte'
    MODE_CHOICES = [
        (ESPECES, 'Espèces'),
        (MOBILE_MONEY, 'Mobile Money'),
        (CARTE, 'Carte bancaire'),
    ]

    facture = models.OneToOneField(Facture, on_delete=models.CASCADE, related_name='paiement')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    mode_paiement = models.CharField(max_length=20, choices=MODE_CHOICES, default=ESPECES)
    date_paiement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement de {self.montant} FCFA ({self.get_mode_paiement_display()})"
