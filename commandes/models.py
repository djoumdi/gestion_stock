# commandes/models.py
from django.conf import settings
from django.db import models
from clients.models import Client
from stock.models import Produit


class CompteClient(models.Model):
    """Relie un compte de connexion (User) à une fiche Client existante.
    Garde le système d'authentification du portail totalement séparé des
    permissions Django utilisées par le staff (Administrateur, Gestionnaire
    de stock, Magasinier, Caissier) : un CompteClient n'appartient à aucun
    de ces groupes, donc perms.* renvoie toujours False pour lui — il n'a
    accès qu'aux vues du portail, jamais à l'admin ni aux vues staff."""
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='compte_client')
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='compte_client')
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Compte client de {self.client.nom}"


class CommandeClient(models.Model):
    EN_ATTENTE = 'EN_ATTENTE'
    CONFIRMEE = 'CONFIRMEE'
    ASSIGNEE = 'ASSIGNEE'
    EN_LIVRAISON = 'EN_LIVRAISON'
    LIVREE = 'LIVREE'
    VALIDEE = 'VALIDEE'
    ANNULEE = 'ANNULEE'
    STATUT_CHOICES = [
        (EN_ATTENTE, 'En attente de confirmation'),
        (CONFIRMEE, 'Confirmée'),
        (ASSIGNEE, 'Assignée à un livreur'),
        (EN_LIVRAISON, 'En livraison'),
        (LIVREE, 'Livrée — en attente de validation client'),
        (VALIDEE, 'Validée par le client'),
        (ANNULEE, 'Annulée'),
    ]

    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='commandes_portail')
    vente = models.OneToOneField('ventes.Vente', on_delete=models.SET_NULL, null=True, blank=True, related_name='commande_portail')
    livreur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='livraisons_assignees')

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=EN_ATTENTE)
    adresse_livraison = models.CharField(max_length=255)
    telephone_contact = models.CharField(max_length=20, blank=True)
    notes_client = models.TextField(blank=True)

    date_commande = models.DateTimeField(auto_now_add=True)
    date_confirmation = models.DateTimeField(null=True, blank=True)
    date_assignation = models.DateTimeField(null=True, blank=True)
    date_livraison = models.DateTimeField(null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    # Preuve de livraison : facultative, à l'initiative du client (voir
    # discussion produit — la confirmation seule suffit à valider).
    photo_livraison = models.ImageField(upload_to='livraisons/', null=True, blank=True)
    video_livraison = models.FileField(upload_to='livraisons/', null=True, blank=True)

    class Meta:
        ordering = ['-date_commande']

    @property
    def code(self):
        return f"CMD-{self.pk:06d}" if self.pk else "CMD-EN COURS"

    @property
    def total(self):
        return sum(ligne.sous_total for ligne in self.lignes.all())

    def __str__(self):
        return self.code


class LigneCommandeClient(models.Model):
    commande = models.ForeignKey(CommandeClient, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField()
    # Capturé au moment de la commande : si le prix change ensuite, l'ancienne
    # commande garde le prix affiché au client au moment où il a commandé.
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire

    def save(self, *args, **kwargs):
        if not self.prix_unitaire:
            self.prix_unitaire = self.produit.prix_vente
        super().save(*args, **kwargs)
