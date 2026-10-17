from django.apps import AppConfig

# ici ont peut mettre des configurations pour l'application accounts, comme le nom de l'application, le nom de la base de données, etc.
class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from . import signals  # noqa: F401 — branche les signaux connexion/déconnexion 