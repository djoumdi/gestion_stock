from django.db import migrations


PERMS_PAR_GROUPE = {
    'Gestionnaire de stock': ['delete_produit', 'delete_fournisseur'],
    'Vendeur': ['delete_client'],
    'Administrateur': ['delete_produit', 'delete_fournisseur', 'delete_client'],
}


def ajouter_permissions_suppression(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    for nom_groupe, codenames in PERMS_PAR_GROUPE.items():
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            permissions = Permission.objects.filter(codename__in=codenames)
            groupe.permissions.add(*permissions)


def retirer_permissions_suppression(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    for nom_groupe, codenames in PERMS_PAR_GROUPE.items():
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            permissions = Permission.objects.filter(codename__in=codenames)
            groupe.permissions.remove(*permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_add_historique_permissions'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions_suppression, retirer_permissions_suppression),
    ]
