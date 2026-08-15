from django.db import migrations
from ._permissions_utils import forcer_creation_permissions


CODENAMES = ['view_parametresmagasin', 'change_parametresmagasin']


def ajouter_permissions_parametres(apps, schema_editor):
    forcer_creation_permissions(apps, schema_editor)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    groupe = Group.objects.filter(name='Administrateur').first()
    if groupe:
        permissions = Permission.objects.filter(
            codename__in=CODENAMES, content_type__app_label='parametres'
        )
        groupe.permissions.add(*permissions)


def retirer_permissions_parametres(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    groupe = Group.objects.filter(name='Administrateur').first()
    if groupe:
        permissions = Permission.objects.filter(
            codename__in=CODENAMES, content_type__app_label='parametres'
        )
        groupe.permissions.remove(*permissions)


class Migration(migrations.Migration):
    """Sans cette migration, même le groupe Administrateur n'a pas accès à
    /parametres/ : l'app 'parametres' a été créée après le Permission.objects.all()
    initial de accounts.0001_create_groups, donc ses permissions n'y étaient
    jamais incluses (même souci que 0011_add_auth_user_permissions)."""

    dependencies = [
        ('accounts', '0012_renommer_roles_magasinier_caissier'),
        ('parametres', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ajouter_permissions_parametres, retirer_permissions_parametres),
    ]
