from django.db import migrations
from ._permissions_utils import forcer_creation_permissions


CODENAMES_LIVREUR = ['view_commandeclient', 'change_commandeclient']
CODENAMES_STAFF_COMMANDES = ['view_commandeclient', 'change_commandeclient', 'add_vente', 'change_produit']


def ajouter_role_livreur(apps, schema_editor):
    forcer_creation_permissions(apps, schema_editor)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    livreur, _ = Group.objects.get_or_create(name='Livreur')
    livreur.permissions.set(Permission.objects.filter(codename__in=CODENAMES_LIVREUR))

    # Gestionnaire de stock et Caissier peuvent rÃ©ceptionner/confirmer une
    # commande passÃ©e depuis le portail client et l'assigner Ã  un livreur.
    for nom_groupe in ['Gestionnaire de stock', 'Caissier']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            permissions = Permission.objects.filter(codename__in=['view_commandeclient', 'change_commandeclient'])
            groupe.permissions.add(*permissions)

    administrateur = Group.objects.filter(name='Administrateur').first()
    if administrateur:
        administrateur.permissions.set(Permission.objects.all())


def retirer_role_livreur(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    Group.objects.filter(name='Livreur').delete()

    permissions = Permission.objects.filter(codename__in=['view_commandeclient', 'change_commandeclient'])
    for nom_groupe in ['Gestionnaire de stock', 'Caissier']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            groupe.permissions.remove(*permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_permission_reception_magasinier_admin'),
        ('commandes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ajouter_role_livreur, retirer_role_livreur),
    ]
