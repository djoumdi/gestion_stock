# accounts/notifications.py
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Notification, HistoriqueAction


def notifier_utilisateur(utilisateur, message, lien=''):
    """Envoie une notification à une seule personne (ex: confirmation de sa propre action)."""
    Notification.objects.create(destinataire=utilisateur, message=message, lien=lien)


def notifier_administrateurs(message, lien='', exclure=None):
    """Envoie une notification à tous les Administrateurs + superutilisateurs.
    'exclure' évite de notifier deux fois la personne qui vient d'agir si elle est elle-même admin."""
    User = get_user_model()
    destinataires = User.objects.filter(
        Q(groups__name='Administrateur') | Q(is_superuser=True)
    ).distinct()

    if exclure:
        destinataires = destinataires.exclude(pk=exclure.pk)

    Notification.objects.bulk_create([
        Notification(destinataire=u, message=message, lien=lien) for u in destinataires
    ])


def enregistrer_action(utilisateur, action, lien=''):
    """Trace une action dans l'historique/audit log. Ne bloque jamais le flux appelant en cas d'erreur."""
    try:
        HistoriqueAction.objects.create(utilisateur=utilisateur, action=action, lien=lien)
    except Exception:
        pass
