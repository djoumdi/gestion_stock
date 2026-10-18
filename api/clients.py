# api/clients.py
from rest_framework.response import Response
from rest_framework.views import APIView

from clients.models import Client

from .permissions import PermissionDjangoParCodename


class ClientListView(APIView):
    """Liste des clients (sans pagination), pour la liste déroulante des ventes."""
    permission_classes = [PermissionDjangoParCodename]
    permission_lecture = 'clients.view_client'

    def get(self, request):
        return Response(list(Client.objects.order_by('nom').values('id', 'nom')))
