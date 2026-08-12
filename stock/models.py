# stock/models.py
from django.db import models


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
    nom = models.CharField(max_length=200)
    marque = models.ForeignKey(Marque, on_delete=models.SET_NULL, null=True, blank=True, related_name='produits')
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.SET_NULL, null=True, blank=True, related_name='produits')
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, related_name='produits')
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2)
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_stock = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField(default=5)
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.marque} {self.nom}" if self.marque else self.nom

    @property
    def en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte


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
