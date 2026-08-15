# accounts/migrations/0002_add_fournisseur_permissions.py
from django.db import migrations
from ._permissions_utils import forcer_creation_permissions


def ajouter_permissions_fournisseur(apps, schema_editor):
    forcer_creation_permissions(apps, schema_editor)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    gestionnaire = Group.objects.filter(name='Gestionnaire de stock').first()
    if gestionnaire:
        codenames = ['add_fournisseur', 'change_fournisseur', 'view_fournisseur']
        permissions = Permission.objects.filter(codename__in=codenames)
        gestionnaire.permissions.add(*permissions)

    responsable = Group.objects.filter(name='Responsable').first()
    if responsable:
        permission = Permission.objects.filter(codename='view_fournisseur').first()
        if permission:
            responsable.permissions.add(permission)


def retirer_permissions_fournisseur(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    codenames = ['add_fournisseur', 'change_fournisseur', 'view_fournisseur']
    permissions = Permission.objects.filter(codename__in=codenames)

    for nom_groupe in ['Gestionnaire de stock', 'Responsable']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            groupe.permissions.remove(*permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_create_groups'),
        ('fournisseurs', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions_fournisseur, retirer_permissions_fournisseur),
    ]
