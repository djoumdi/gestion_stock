# accounts/migrations/0005_add_inventaire_permissions.py
from django.db import migrations


def ajouter_permissions_inventaire(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    # Seul le Gestionnaire de stock peut RÉELLEMENT créer/gérer des inventaires
    gestionnaire = Group.objects.filter(name='Gestionnaire de stock').first()
    if gestionnaire:
        codenames = [
            'add_inventaire', 'view_inventaire', 'change_inventaire',
            'add_ligneinventaire', 'view_ligneinventaire', 'change_ligneinventaire',
        ]
        permissions = Permission.objects.filter(codename__in=codenames)
        gestionnaire.permissions.add(*permissions)

    # Le Responsable peut seulement consulter
    responsable = Group.objects.filter(name='Responsable').first()
    if responsable:
        codenames = ['view_inventaire', 'view_ligneinventaire']
        permissions = Permission.objects.filter(codename__in=codenames)
        responsable.permissions.add(*permissions)


def retirer_permissions_inventaire(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    codenames = [
        'add_inventaire', 'view_inventaire', 'change_inventaire',
        'add_ligneinventaire', 'view_ligneinventaire', 'change_ligneinventaire',
    ]
    permissions = Permission.objects.filter(codename__in=codenames)

    for nom_groupe in ['Gestionnaire de stock', 'Responsable']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            groupe.permissions.remove(*permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_facture_paiement_permissions'),
        ('stock', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions_inventaire, retirer_permissions_inventaire),
    ]
