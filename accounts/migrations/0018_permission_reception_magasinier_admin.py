from django.db import migrations


def accorder_permission_reception(apps, schema_editor):
    """Crée (si besoin) la permission receptionner_achat et l'accorde au
    Magasinier et à l'Administrateur. On ne passe PAS par create_permissions()
    pour tout le projet : on ne crée que cette permission-là, ce qui évite une
    longue série de requêtes dans la transaction."""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Group = apps.get_model('auth', 'Group')

    type_contenu, _ = ContentType.objects.get_or_create(app_label='achats', model='achat')
    permission, _ = Permission.objects.get_or_create(
        codename='receptionner_achat',
        content_type=type_contenu,
        defaults={'name': 'Peut réceptionner une commande (mise à jour du stock)'},
    )

    for nom_groupe in ['Magasinier', 'Administrateur']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            groupe.permissions.add(permission)


def retirer_permission_reception(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    permission = Permission.objects.filter(codename='receptionner_achat').first()
    if not permission:
        return

    for nom_groupe in ['Magasinier', 'Administrateur']:
        groupe = Group.objects.filter(name=nom_groupe).first()
        if groupe:
            groupe.permissions.remove(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_historiqueaction_type_action_adresse_ip'),
        ('achats', '0004_achat_permission_reception'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(accorder_permission_reception, retirer_permission_reception),
    ]