# api/serializers.py
from rest_framework import serializers

from stock.models import Produit

# Champs réservés à ceux qui gèrent le stock : le prix d'achat et la marge
# ne sont jamais envoyés au caissier ou au magasinier.
CHAMPS_CONFIDENTIELS = ('prix_achat', 'marge', 'taux_marge')


class ProduitSerializer(serializers.ModelSerializer):
    marque = serializers.SerializerMethodField()
    fournisseur = serializers.SerializerMethodField()
    categorie = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    en_alerte = serializers.BooleanField(read_only=True)
    en_surstock = serializers.BooleanField(read_only=True)
    marge = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    taux_marge = serializers.FloatField(read_only=True, allow_null=True)

    class Meta:
        model = Produit
        fields = [
            'id', 'reference', 'code_barres', 'nom', 'description',
            'marque', 'categorie', 'fournisseur',
            'prix_vente', 'prix_achat', 'marge', 'taux_marge',
            'quantite_stock', 'seuil_alerte', 'seuil_max',
            'en_alerte', 'en_surstock', 'image_url',
        ]

    def get_marque(self, obj):
        return obj.marque.nom if obj.marque else None

    def get_fournisseur(self, obj):
        return obj.fournisseur.nom if obj.fournisseur else None

    def get_categorie(self, obj):
        if not obj.categorie:
            return None
        return {'id': obj.categorie.id, 'nom': obj.categorie.nom}

    def get_image_url(self, obj):
        if not obj.image:
            return None
        url = obj.image.url
        requete = self.context.get('request')
        return requete.build_absolute_uri(url) if requete else url

    def to_representation(self, instance):
        donnees = super().to_representation(instance)
        requete = self.context.get('request')
        peut_voir_marges = bool(
            requete and requete.user.is_authenticated
            and requete.user.has_perm('stock.change_produit')
        )
        if not peut_voir_marges:
            for champ in CHAMPS_CONFIDENTIELS:
                donnees.pop(champ, None)
        return donnees
