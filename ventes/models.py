# ventes/models.py
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from stock.models import Produit


class Vente(models.Model):
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, related_name='ventes')
    vendeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventes_effectuees')
    date_vente = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Vente #{self.id} - {self.date_vente.strftime('%d/%m/%Y')}"

    @property
    def code(self):
        return f"VTE-{self.pk:06d}" if self.pk else "VTE-EN COURS"

    @property
    def total(self):
        return sum(ligne.sous_total for ligne in self.lignes.all())


class Devis(models.Model):
    EN_ATTENTE = 'EN_ATTENTE'
    ACCEPTE = 'ACCEPTE'
    REFUSE = 'REFUSE'
    CONVERTI = 'CONVERTI'
    STATUT_CHOICES = [
        (EN_ATTENTE, 'En attente'),
        (ACCEPTE, 'Accepté'),
        (REFUSE, 'Refusé'),
        (CONVERTI, 'Converti en vente'),
    ]

    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, related_name='devis')
    vendeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='devis_crees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validite = models.DateField(null=True, blank=True, help_text="Date jusqu'à laquelle le devis est valable. Optionnel.")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=EN_ATTENTE)
    notes = models.TextField(blank=True)
    # Rempli uniquement au moment de la conversion — trace vers la vente réelle générée.
    vente = models.OneToOneField(Vente, on_delete=models.SET_NULL, null=True, blank=True, related_name='devis_origine')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Devis #{self.id} - {self.date_creation.strftime('%d/%m/%Y')}"

    @property
    def code(self):
        return f"DEV-{self.pk:06d}" if self.pk else "DEV-EN COURS"

    @property
    def total(self):
        return sum(ligne.sous_total for ligne in self.lignes.all())

    @property
    def date_depassee(self):
        """Vérité brute, indépendante du statut : la date de validité est-elle
        dépassée ? Contrairement à est_expire (qui sert juste à l'affichage du
        badge et ne concerne que les devis encore EN_ATTENTE), celle-ci sert
        aux vérifications métier (voir est_convertible) — un devis ACCEPTÉ
        mais dont la date est passée doit rester bloqué à la conversion."""
        from django.utils import timezone
        return bool(self.date_validite) and self.date_validite < timezone.localdate()

    @property
    def est_expire(self):
        # Badge "Expiré" : uniquement pertinent tant que le devis est encore
        # EN_ATTENTE d'une réponse — un devis déjà accepté/refusé/converti
        # affiche son propre statut plutôt que "Expiré".
        return self.date_depassee and self.statut == self.EN_ATTENTE

    @property
    def est_convertible(self):
        # Seul un devis ACCEPTÉ par le client peut devenir une vente — c'est
        # l'acceptation du client qui déclenche la conversion, jamais le simple
        # fait d'être "en attente". Voir convertir_devis() dans views.py.
        # Un devis expiré ne doit jamais être convertible, même s'il a été
        # accepté avant sa date de péremption : les prix ont pu changer entre
        # temps, il faut le refaire plutôt que de vendre sur un prix figé obsolète.
        return self.statut == self.ACCEPTE and not self.date_depassee


class LigneDevis(models.Model):
    devis = models.ForeignKey(Devis, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire

    def save(self, *args, **kwargs):
        if not self.prix_unitaire:
            self.prix_unitaire = self.produit.prix_vente
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom}"


class LigneVente(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire

    @property
    def quantite_deja_retournee(self):
        return self.retours.aggregate(total=models.Sum('quantite'))['total'] or 0

    @property
    def quantite_retournable(self):
        return self.quantite - self.quantite_deja_retournee

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


class Retour(models.Model):
    """Un retour = un ou plusieurs produits d'UNE vente rapportés par le
    client. Crée automatiquement les mouvements de stock ENTREE correspondants
    et sert de justificatif d'avoir (montant à rembourser ou à déduire d'un
    prochain achat — la gestion d'un solde crédit client n'est volontairement
    PAS implémentée ici, un avoir reste un document, pas un porte-monnaie
    électronique à faire évoluer plus tard si besoin)."""
    vente = models.ForeignKey(Vente, on_delete=models.PROTECT, related_name='retours')
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='retours_crees')
    motif = models.TextField()
    date_retour = models.DateTimeField(auto_now_add=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        ordering = ['-date_retour']

    def __str__(self):
        return f"Retour #{self.id} sur {self.vente.code}"

    @property
    def code(self):
        return f"AVR-{self.pk:06d}" if self.pk else "AVR-EN COURS"

    @property
    def total(self):
        return sum(ligne.sous_total for ligne in self.lignes.all())


class LigneRetour(models.Model):
    retour = models.ForeignKey(Retour, on_delete=models.CASCADE, related_name='lignes')
    ligne_vente = models.ForeignKey(LigneVente, on_delete=models.PROTECT, related_name='retours')
    quantite = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    @property
    def produit(self):
        return self.ligne_vente.produit

    @property
    def prix_unitaire(self):
        return self.ligne_vente.prix_unitaire

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom} (retour)"
