# api/ventes.py
from datetime import date as date_type

from django.db import transaction
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.response import Response

from accounts.notifications import enregistrer_action
from clients.models import Client
from stock.models import MouvementStock, Produit
from ventes.models import Facture, LigneVente, Vente

from .permissions import PermissionDjangoParCodename


class VenteListeSerializer(serializers.ModelSerializer):
    code = serializers.CharField(read_only=True)
    client = serializers.SerializerMethodField()
    vendeur = serializers.SerializerMethodField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    nb_lignes = serializers.SerializerMethodField()

    class Meta:
        model = Vente
        fields = ['id', 'code', 'date_vente', 'client', 'vendeur', 'total', 'nb_lignes']

    def get_client(self, obj):
        return obj.client.nom if obj.client else None

    def get_vendeur(self, obj):
        return obj.vendeur.username if obj.vendeur else None

    def get_nb_lignes(self, obj):
        return len(obj.lignes.all())


class VenteDetailSerializer(VenteListeSerializer):
    lignes = serializers.SerializerMethodField()
    facture = serializers.SerializerMethodField()

    class Meta(VenteListeSerializer.Meta):
        fields = VenteListeSerializer.Meta.fields + ['lignes', 'facture']

    def get_lignes(self, obj):
        return [
            {
                'produit_id': ligne.produit_id,
                'produit': ligne.produit.nom,
                'quantite': ligne.quantite,
                'prix_unitaire': str(ligne.prix_unitaire),
                'sous_total': str(ligne.sous_total),
            }
            for ligne in obj.lignes.all()
        ]

    def get_facture(self, obj):
        facture = getattr(obj, 'facture', None)
        if facture is None:
            return None
        return {'numero': facture.numero, 'est_payee': facture.est_payee}


class VenteViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Liste, fiche et création des ventes.

    Création (POST /api/ventes/) :
      {
        "client": 3,                       (optionnel, null = client anonyme)
        "lignes": [{"produit": 1, "quantite": 2}, ...]
      }
    Le serveur vérifie le stock, enregistre la vente, les lignes, les mouvements
    de stock et la facture dans une seule transaction.
    """
    permission_classes = [PermissionDjangoParCodename]
    permission_lecture = 'ventes.view_vente'
    permission_ecriture = 'ventes.add_vente'
    queryset = (
        Vente.objects.select_related('client', 'vendeur')
        .prefetch_related('lignes__produit')
        .order_by('-date_vente')
    )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VenteDetailSerializer
        return VenteListeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        utilisateur = self.request.user

        voit_tout = utilisateur.is_superuser or utilisateur.groups.filter(name='Administrateur').exists()
        if not voit_tout:
            qs = qs.filter(vendeur=utilisateur)

        parametres = self.request.query_params

        recherche = parametres.get('q', '').strip()
        if recherche:
            qs = qs.filter(client__nom__icontains=recherche)

        jour = parametres.get('date')
        if jour:
            try:
                qs = qs.filter(date_vente__date=date_type.fromisoformat(jour))
            except ValueError:
                pass

        return qs

    def create(self, request, *args, **kwargs):
        donnees = request.data
        lignes_brutes = donnees.get('lignes') or []
        if not isinstance(lignes_brutes, list) or not lignes_brutes:
            return Response({'detail': "Ajoutez au moins un produit à la vente."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Nettoyage des lignes et cumul des quantités par produit
        cumul = {}
        for ligne in lignes_brutes:
            try:
                produit_id = int(ligne.get('produit'))
                quantite = int(ligne.get('quantite'))
            except (TypeError, ValueError, AttributeError):
                return Response({'detail': "Produit ou quantité invalide."}, status=status.HTTP_400_BAD_REQUEST)
            if quantite <= 0:
                return Response({'detail': "La quantité doit être supérieure à zéro."}, status=status.HTTP_400_BAD_REQUEST)
            cumul[produit_id] = cumul.get(produit_id, 0) + quantite

        # 2. Client optionnel
        client = None
        if donnees.get('client'):
            try:
                client = Client.objects.get(pk=int(donnees['client']))
            except (Client.DoesNotExist, TypeError, ValueError):
                return Response({'detail': "Client introuvable."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Tout dans une transaction : si une étape échoue, rien n'est enregistré
        with transaction.atomic():
            # select_for_update : verrouille les produits pendant la vente,
            # pour que deux caissiers ne vendent pas le même stock en même temps
            produits = {p.pk: p for p in Produit.objects.select_for_update().filter(pk__in=cumul.keys())}
            if len(produits) != len(cumul):
                return Response({'detail': "Un ou plusieurs produits sont introuvables."}, status=status.HTTP_400_BAD_REQUEST)

            insuffisants = [
                f"{produits[pid].nom} (demandé {quantite}, disponible {produits[pid].quantite_stock})"
                for pid, quantite in cumul.items()
                if quantite > produits[pid].quantite_stock
            ]
            if insuffisants:
                return Response(
                    {'detail': "Stock insuffisant : " + ", ".join(insuffisants)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            vente = Vente.objects.create(client=client, vendeur=request.user)
            for pid, quantite in cumul.items():
                produit = produits[pid]
                LigneVente.objects.create(
                    vente=vente,
                    produit=produit,
                    quantite=quantite,
                    prix_unitaire=produit.prix_vente,
                )
                # Le mouvement de sortie met aussi à jour le stock (comme dans l'application actuelle)
                MouvementStock.objects.create(
                    produit=produit,
                    type_mouvement=MouvementStock.SORTIE,
                    quantite=quantite,
                    motif=f"Vente {vente.code}",
                )
            Facture.objects.create(vente=vente)

        enregistrer_action(request.user, f"a enregistré la vente {vente.code} (application React)")
        return Response(VenteDetailSerializer(vente, context={'request': request}).data, status=status.HTTP_201_CREATED)
