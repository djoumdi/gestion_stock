# accounts/migrations/0001_create_groups.py
from django.db import migrations


def creer_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    gestionnaire, _ = Group.objects.get_or_create(name='Gestionnaire de stock')
    codenames_gestionnaire = [
        'add_produit', 'change_produit', 'view_produit',
        'add_categorie', 'change_categorie', 'delete_categorie', 'view_categorie',
        'add_marque', 'change_marque', 'delete_marque', 'view_marque',
        'add_mouvementstock', 'view_mouvementstock',
    ]
    permissions = Permission.objects.filter(codename__in=codenames_gestionnaire)
    gestionnaire.permissions.set(permissions)

    vendeur, _ = Group.objects.get_or_create(name='Vendeur')
    codenames_vendeur = [
        'view_produit',
        'add_client', 'change_client', 'view_client',
        'add_vente', 'view_vente',
        'add_lignevente', 'view_lignevente',
    ]
    permissions = Permission.objects.filter(codename__in=codenames_vendeur)
    vendeur.permissions.set(permissions)

    responsable, _ = Group.objects.get_or_create(name='Responsable')
    codenames_responsable = [
        'view_produit', 'view_categorie', 'view_marque',
        'view_client', 'view_vente', 'view_lignevente', 'view_mouvementstock',
    ]
    permissions = Permission.objects.filter(codename__in=codenames_responsable)
    responsable.permissions.set(permissions)

    administrateur, _ = Group.objects.get_or_create(name='Administrateur')
    administrateur.permissions.set(Permission.objects.all())


def supprimer_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(
        name__in=['Gestionnaire de stock', 'Vendeur', 'Responsable', 'Administrateur']
    ).delete()


class Migration(migrations.Migration):

    # Dépend maintenant de plusieurs apps (client/vente ont déménagé hors de stock)
    dependencies = [
        ('stock', '0001_initial'),
        ('clients', '0001_initial'),
        ('ventes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(creer_roles, supprimer_roles),
    ]
