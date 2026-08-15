from django.db import migrations
from ._permissions_utils import forcer_creation_permissions


def ajouter_permissions_historique(apps, schema_editor):
    forcer_creation_permissions(apps, schema_editor)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    permission = Permission.objects.get(codename='view_historiqueaction')

    for nom_groupe in ['Administrateur', 'Responsable']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            groupe.permissions.add(permission)


def retirer_permissions_historique(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    permission = Permission.objects.filter(codename='view_historiqueaction').first()
    if permission:
        for nom_groupe in ['Administrateur', 'Responsable']:
            groupe = Group.objects.filter(name=nom_groupe).first()
            if groupe:
                groupe.permissions.remove(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_historiqueaction'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions_historique, retirer_permissions_historique),
    ]
