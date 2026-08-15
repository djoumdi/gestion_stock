# accounts/migrations/_permissions_utils.py
#
# Ce fichier n'est PAS une migration (pas de classe Migration ni de fonction
# "operations") : Django ne l'exécutera donc jamais tout seul, il sert juste
# d'utilitaire partagé importé par les migrations qui en ont besoin.
#
# Pourquoi ce fichier existe : Django ne crée les permissions (add_/change_/
# delete_/view_<modele>) d'un modèle qu'à la toute fin de la commande
# "migrate" (signal post_migrate), une seule fois pour TOUTES les apps, APRÈS
# que toutes les migrations du plan ont été appliquées. Résultat : sur une
# base de données migrée d'un coup depuis zéro (clone frais du dépôt, poste
# d'un correcteur, nouveau collaborateur...), une migration de données qui
# attribue des permissions à un groupe juste après avoir créé le modèle
# correspondant s'exécute AVANT que ces permissions existent en base.
#
# Avec Permission.objects.get(...), ça plante (Permission.DoesNotExist).
# Avec Permission.objects.filter(...), ça ne plante pas mais silencieusement
# n'attribue AUCUNE permission — encore pire, car ça ne se voit pas tout de
# suite.
from django.contrib.auth.management import create_permissions


def forcer_creation_permissions(apps, schema_editor):
    """À appeler en tout premier dans une migration de données qui va
    ensuite chercher des Permission fraîchement créées par une migration
    CreateModel précédente. Force Django à créer immédiatement les
    permissions de toutes les apps plutôt que d'attendre la fin de
    "migrate". Idempotent (get_or_create en interne côté Django) : aucun
    risque à l'appeler plusieurs fois dans la même exécution."""
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, verbosity=0, using=schema_editor.connection.alias)
        app_config.models_module = None
