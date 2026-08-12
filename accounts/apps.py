from django.apps import AppConfig

# ici ont peut mettre des configurations pour l'application accounts, comme le nom de l'application, le nom de la base de données, etc.
class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts' 