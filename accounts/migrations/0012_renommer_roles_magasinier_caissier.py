from django.db import migrations
from ._permissions_utils import forcer_creation_permissions


# Permissions du Magasinier, telles que définies dans le cahier des charges :
# "Réception des commandes, saisie des mouvements de stock, consultation des produits".
# Volontairement DIFFÉRENT de l'ancien groupe "Responsable" (lecture seule sur tout) :
# le Magasinier a un vrai droit d'action sur les réceptions et les mouvements,
# mais PAS sur la création de commandes (ça reste au Gestionnaire de stock) ni
# sur les inventaires (pas dans son périmètre selon le cahier des charges).
CODENAMES_MAGASINIER = [
    'view_produit',
    'view_mouvementstock', 'add_mouvementstock',
    'view_achat', 'change_achat',
]


def renommer_roles(apps, schema_editor):
    forcer_creation_permissions(apps, schema_editor)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    # Vendeur -> Caissier : même métier, juste le nom qui s'aligne sur le
    # cahier des charges. Les permissions ne changent pas.
    vendeur = Group.objects.filter(name='Vendeur').first()
    if vendeur:
        vendeur.name = 'Caissier'
        vendeur.save()

    # Responsable -> Magasinier : ATTENTION, ce n'est pas qu'un renommage.
    # "Responsable" était un rôle de supervision en lecture seule (absent du
    # cahier des charges). "Magasinier" est un rôle opérationnel différent
    # (réception + mouvements de stock). On repart donc d'un jeu de
    # permissions propre plutôt que de garder l'ancien.
    responsable = Group.objects.filter(name='Responsable').first()
    if responsable:
        responsable.name = 'Magasinier'
        responsable.save()
        responsable.permissions.clear()
        permissions = Permission.objects.filter(codename__in=CODENAMES_MAGASINIER)
        responsable.permissions.set(permissions)


def annuler_renommage(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    caissier = Group.objects.filter(name='Caissier').first()
    if caissier:
        caissier.name = 'Vendeur'
        caissier.save()

    magasinier = Group.objects.filter(name='Magasinier').first()
    if magasinier:
        magasinier.name = 'Responsable'
        magasinier.save()
        magasinier.permissions.clear()
        codenames_responsable = [
            'view_produit', 'view_categorie', 'view_marque',
            'view_client', 'view_vente', 'view_lignevente', 'view_mouvementstock',
            'view_fournisseur', 'view_achat', 'view_ligneachat',
            'view_facture', 'view_paiement',
            'view_inventaire', 'view_ligneinventaire',
        ]
        permissions = Permission.objects.filter(codename__in=codenames_responsable)
        magasinier.permissions.set(permissions)


class Migration(migrations.Migration):
    """Réaligne les groupes Django sur les 4 rôles officiels du cahier des
    charges (Administrateur, Gestionnaire de stock, Magasinier, Caissier).
    Tout utilisateur déjà dans 'Vendeur' ou 'Responsable' bascule
    automatiquement dans le groupe renommé (c'est le même objet Group, donc
    la relation ManyToMany user<->group n'est pas touchée) — mais le
    Magasinier récupère un jeu de permissions différent de l'ancien
    Responsable, voir plus haut."""

    dependencies = [
        ('accounts', '0011_add_auth_user_permissions'),
    ]

    operations = [
        migrations.RunPython(renommer_roles, annuler_renommage),
    ]
