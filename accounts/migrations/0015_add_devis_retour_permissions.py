from django.db import migrations
from ._permissions_utils import forcer_creation_permissions


CODENAMES_CAISSIER = [
    'add_devis', 'view_devis', 'change_devis',
    'add_lignedevis', 'view_lignedevis', 'change_lignedevis',
    'add_retour', 'view_retour',
    'add_ligneretour', 'view_ligneretour',
]


def ajouter_permissions(apps, schema_editor):
    forcer_creation_permissions(apps, schema_editor)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    caissier = Group.objects.filter(name='Caissier').first()
    if caissier:
        permissions = Permission.objects.filter(codename__in=CODENAMES_CAISSIER)
        caissier.permissions.add(*permissions)


def retirer_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    caissier = Group.objects.filter(name='Caissier').first()
    if caissier:
        permissions = Permission.objects.filter(codename__in=CODENAMES_CAISSIER)
        caissier.permissions.remove(*permissions)


class Migration(migrations.Migration):
    """Le Caissier gère devis et retours, comme les ventes classiques. Sans
    cette migration, personne (hors Administrateur) n'aurait accès aux pages
    devis/retours, même si les vues et templates existent."""

    dependencies = [
        ('accounts', '0014_preferenceutilisateur'),
        ('ventes', '0004_devis_retours'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions, retirer_permissions),
    ]
