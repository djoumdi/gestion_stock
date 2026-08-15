# stock/models.py
from django.db import models
from django.conf import settings


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name_plural = "Catégories"


class Marque(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom


class Produit(models.Model):
    reference = models.CharField(max_length=50, unique=True, blank=True,
        help_text="Référence interne (SKU). Générée automatiquement si laissée vide.")
    code_barres = models.CharField(max_length=50, blank=True,
        help_text="Code EAN/UPC scanné ou saisi manuellement. Optionnel.")
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    marque = models.ForeignKey(Marque, on_delete=models.SET_NULL, null=True, blank=True, related_name='produits')
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.SET_NULL, null=True, blank=True, related_name='produits')
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, related_name='produits')
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2)
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_stock = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=5, help_text="Seuil de stock MINIMUM avant alerte.")
    seuil_max = models.PositiveIntegerField(null=True, blank=True, help_text="Seuil de stock MAXIMUM recommandé (optionnel).")
    date_ajout = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.reference:
            self.reference = f"PRD-{self.pk:06d}"
            super().save(update_fields=['reference'])

    def __str__(self):
        return f"{self.marque} {self.nom}" if self.marque else self.nom

    @property
    def en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte

    @property
    def en_surstock(self):
        return self.seuil_max is not None and self.quantite_stock > self.seuil_max

    @property
    def marge(self):
        return self.prix_vente - self.prix_achat

    @property
    def taux_marge(self):
        """Marge en % du prix d'achat. None si prix_achat vaut 0 (division impossible)."""
        if self.prix_achat:
            return round((self.marge / self.prix_achat) * 100, 1)
        return None


class MouvementStock(models.Model):
    ENTREE = 'entree'
    SORTIE = 'sortie'
    TYPE_CHOICES = [(ENTREE, 'Entrée'), (SORTIE, 'Sortie')]

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite = models.PositiveIntegerField()
    motif = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            if self.type_mouvement == self.ENTREE:
                self.produit.quantite_stock += self.quantite
            else:
                self.produit.quantite_stock -= self.quantite
            self.produit.save()

    def __str__(self):
        return f"{self.type_mouvement} - {self.quantite} - {self.produit.nom}"


class Inventaire(models.Model):
    EN_COURS = 'EN_COURS'
    VALIDE = 'VALIDE'
    STATUT_CHOICES = [
        (EN_COURS, 'En cours'),
        (VALIDE, 'Validé'),
    ]

    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='inventaires_crees')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=EN_COURS)
    date_validation = models.DateTimeField(null=True, blank=True)

    @property
    def code(self):
        return f"INV-{self.pk:06d}" if self.pk else "INV-EN COURS"

    def __str__(self):
        return self.code


class LigneInventaire(models.Model):
    inventaire = models.ForeignKey(Inventaire, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite_theorique = models.IntegerField()
    quantite_physique = models.IntegerField(null=True, blank=True)

    @property
    def ecart(self):
        if self.quantite_physique is None:
            return None
        return self.quantite_physique - self.quantite_theorique

    def __str__(self):
        return f"{self.produit.nom} (théorique {self.quantite_theorique})"
