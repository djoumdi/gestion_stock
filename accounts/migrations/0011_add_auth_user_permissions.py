from django.db import migrations
from ._permissions_utils import forcer_creation_permissions


CODENAMES = ['add_user', 'change_user', 'view_user']


def ajouter_permissions_utilisateurs(apps, schema_editor):
    forcer_creation_permissions(apps, schema_editor)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    groupe = Group.objects.filter(name='Administrateur').first()
    if groupe:
        permissions = Permission.objects.filter(codename__in=CODENAMES, content_type__app_label='auth')
        groupe.permissions.add(*permissions)


def retirer_permissions_utilisateurs(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    groupe = Group.objects.filter(name='Administrateur').first()
    if groupe:
        permissions = Permission.objects.filter(codename__in=CODENAMES, content_type__app_label='auth')
        groupe.permissions.remove(*permissions)


class Migration(migrations.Migration):
    """Sans cette migration, un compte du groupe Administrateur (mais pas
    superuser) reçoit un 403 sur toutes les pages de gestion des utilisateurs
    (liste_utilisateurs, ajouter_utilisateur, detail_utilisateur), qui exigent
    auth.view_user / auth.add_user / auth.change_user — des permissions
    natives de Django jamais accordées jusqu'ici."""

    dependencies = [
        ('accounts', '0010_add_delete_permissions'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions_utilisateurs, retirer_permissions_utilisateurs),
    ]
