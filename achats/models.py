from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from stock.models import Produit


class Achat(models.Model):
    EN_ATTENTE = 'EN_ATTENTE'
    COMMANDE = 'COMMANDE'
    RECU = 'RECU'
    ANNULE = 'ANNULE'
    STATUT_CHOICES = [
        (EN_ATTENTE, 'En attente'),
        (COMMANDE, 'Commandée'),
        (RECU, 'Reçu'),
        (ANNULE, 'Annulé'),
    ]

    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.SET_NULL, null=True, related_name='achats')
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='achats_crees')
    notes = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=EN_ATTENTE)
    date_achat = models.DateTimeField(auto_now_add=True)

    @property
    def code(self):
        return f"ACH-{self.pk:06d}" if self.pk else "ACH-EN COURS"

    def __str__(self):
        return self.code

    @property
    def total(self):
        return sum(ligne.sous_total for ligne in self.lignes.all())


class LigneAchat(models.Model):
    achat = models.ForeignKey(Achat, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    # Pas de save() qui touche au stock ici : avec le nouveau workflow, le stock
    # n'est mis à jour qu'au moment de la RÉCEPTION (voir valider_reception),
    # pas dès la création de la ligne — un achat "en attente" ne doit rien changer physiquement.

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom}"
