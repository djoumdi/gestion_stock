# api/views.py
from django.db.models import F, Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from stock.models import Categorie, Produit

from .permissions import PermissionDjangoParCodename
from .serializers import ProduitSerializer


class ProduitViewSet(viewsets.ReadOnlyModelViewSet):
    """Liste et fiche des produits.

    Filtres (query string) :
      - q          : recherche sur le nom, la référence ou le code-barres
      - categorie  : identifiant de la catégorie
      - alerte=1   : seulement les produits en stock faible ou en rupture
    """
    serializer_class = ProduitSerializer
    permission_classes = [PermissionDjangoParCodename]
    permission_lecture = 'stock.view_produit'
    queryset = Produit.objects.select_related('marque', 'categorie', 'fournisseur').order_by('nom')

    def get_queryset(self):
        qs = super().get_queryset()
        parametres = self.request.query_params

        recherche = parametres.get('q', '').strip()
        if recherche:
            qs = qs.filter(
                Q(nom__icontains=recherche)
                | Q(reference__icontains=recherche)
                | Q(code_barres__icontains=recherche)
            )

        categorie = parametres.get('categorie')
        if categorie:
            qs = qs.filter(categorie_id=categorie)

        if parametres.get('alerte') == '1':
            qs = qs.filter(quantite_stock__lte=F('seuil_alerte'))

        return qs


class CategorieListView(APIView):
    """Liste des catégories (sans pagination), pour remplir le menu des filtres."""
    permission_classes = [PermissionDjangoParCodename]
    permission_lecture = 'stock.view_produit'

    def get(self, request):
        categories = Categorie.objects.order_by('nom').values('id', 'nom')
        return Response(list(categories))


class MoiView(APIView):
    """Profil du compte connecté et liste de ses permissions."""
    permission_classes = [IsAuthenticated]

    PERMISSIONS_UTILES = [
        'stock.view_produit', 'stock.add_produit', 'stock.change_produit', 'stock.delete_produit',
        'stock.add_mouvementstock', 'stock.view_mouvementstock',
        'achats.add_achat', 'achats.change_achat', 'achats.receptionner_achat',
        'ventes.add_vente', 'ventes.view_vente', 'ventes.add_devis',
        'accounts.view_historiqueaction',
        'parametres.change_parametresmagasin',
    ]

    def get(self, request):
        utilisateur = request.user
        return Response({
            'username': utilisateur.username,
            'nom_complet': utilisateur.get_full_name(),
            'groupes': list(utilisateur.groups.values_list('name', flat=True)),
            'superutilisateur': utilisateur.is_superuser,
            'permissions': [p for p in self.PERMISSIONS_UTILES if utilisateur.has_perm(p)],
        })
