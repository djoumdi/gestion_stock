# api/permissions.py
from rest_framework.permissions import BasePermission


class PermissionDjangoParCodename(BasePermission):
    """Applique à l'API la même matrice de rôles que l'application Django.

    - Lecture (GET) : il faut la permission déclarée dans `permission_lecture`.
    - Écriture (POST) : il faut la permission déclarée dans `permission_ecriture`.
    Une vue qui ne déclare pas `permission_ecriture` refuse donc toute écriture.
    """

    def has_permission(self, request, view):
        utilisateur = request.user
        if not utilisateur or not utilisateur.is_authenticated:
            return False

        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            permission = getattr(view, 'permission_lecture', None)
            return permission is None or utilisateur.has_perm(permission)

        if request.method == 'POST':
            permission = getattr(view, 'permission_ecriture', None)
            return permission is not None and utilisateur.has_perm(permission)

        return False
