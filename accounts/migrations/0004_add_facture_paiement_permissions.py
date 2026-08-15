# accounts/migrations/0004_add_facture_paiement_permissions.py
from django.db import migrations
from ._permissions_utils import forcer_creation_permissions


def ajouter_permissions(apps, schema_editor):
    forcer_creation_permissions(apps, schema_editor)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    vendeur = Group.objects.filter(name='Vendeur').first()
    if vendeur:
        codenames = ['add_facture', 'view_facture', 'add_paiement', 'view_paiement']
        permissions = Permission.objects.filter(codename__in=codenames)
        vendeur.permissions.add(*permissions)

    for nom_groupe in ['Gestionnaire de stock', 'Responsable', 'Administrateur']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            codenames = ['view_facture', 'view_paiement']
            permissions = Permission.objects.filter(codename__in=codenames)
            groupe.permissions.add(*permissions)


def retirer_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    codenames = ['add_facture', 'view_facture', 'add_paiement', 'view_paiement']
    permissions = Permission.objects.filter(codename__in=codenames)

    for nom_groupe in ['Vendeur', 'Gestionnaire de stock', 'Responsable', 'Administrateur']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            groupe.permissions.remove(*permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_add_achat_permissions'),
        ('ventes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions, retirer_permissions),
    ]
