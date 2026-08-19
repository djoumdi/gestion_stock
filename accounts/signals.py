# accounts/signals.py
"""Journalise les connexions, déconnexions et tentatives échouées dans le
même HistoriqueAction que les actions métier — voir models.HistoriqueAction
et notifications.enregistrer_action. Branché depuis AccountsConfig.ready()."""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .models import HistoriqueAction
from .notifications import enregistrer_action


def _adresse_ip(request):
    """Récupère l'IP réelle du client, y compris derrière un proxy/reverse-proxy
    (Nginx, load balancer...) qui renseigne X-Forwarded-For."""
    if request is None:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def journaliser_connexion(sender, request, user, **kwargs):
    enregistrer_action(
        user, "s'est connecté",
        type_action=HistoriqueAction.CONNEXION,
        adresse_ip=_adresse_ip(request),
    )


@receiver(user_logged_out)
def journaliser_deconnexion(sender, request, user, **kwargs):
    # 'user' peut être None si la session était déjà invalide au moment du logout.
    if user is None:
        return
    enregistrer_action(
        user, "s'est déconnecté",
        type_action=HistoriqueAction.CONNEXION,
        adresse_ip=_adresse_ip(request),
    )


@receiver(user_login_failed)
def journaliser_echec_connexion(sender, credentials, request=None, **kwargs):
    identifiant = credentials.get('username', 'inconnu')
    enregistrer_action(
        None, f"tentative de connexion échouée pour l'identifiant « {identifiant} »",
        type_action=HistoriqueAction.CONNEXION,
        adresse_ip=_adresse_ip(request),
    )
