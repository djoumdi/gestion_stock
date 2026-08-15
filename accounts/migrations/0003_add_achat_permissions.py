# accounts/migrations/0003_add_achat_permissions.py
from django.db import migrations
from ._permissions_utils import forcer_creation_permissions


def ajouter_permissions_achat(apps, schema_editor):
    forcer_creation_permissions(apps, schema_editor)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    gestionnaire = Group.objects.filter(name='Gestionnaire de stock').first()
    if gestionnaire:
        codenames = [
            'add_achat', 'view_achat', 'change_achat',
            'add_ligneachat', 'view_ligneachat', 'change_ligneachat', 'delete_ligneachat',
            'add_mouvementstock',
        ]
        permissions = Permission.objects.filter(codename__in=codenames)
        gestionnaire.permissions.add(*permissions)

    responsable = Group.objects.filter(name='Responsable').first()
    if responsable:
        codenames = ['view_achat', 'view_ligneachat']
        permissions = Permission.objects.filter(codename__in=codenames)
        responsable.permissions.add(*permissions)


def retirer_permissions_achat(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    codenames = [
        'add_achat', 'view_achat', 'change_achat',
        'add_ligneachat', 'view_ligneachat', 'change_ligneachat', 'delete_ligneachat',
    ]
    permissions = Permission.objects.filter(codename__in=codenames)

    for nom_groupe in ['Gestionnaire de stock', 'Responsable']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            groupe.permissions.remove(*permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_fournisseur_permissions'),
        ('achats', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions_achat, retirer_permissions_achat),
    ]
