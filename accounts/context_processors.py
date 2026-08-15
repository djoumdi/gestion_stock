# accounts/context_processors.py
from .models import PreferenceUtilisateur


def notifications(request):
    if request.user.is_authenticated:
        qs = request.user.notifications.filter(lue=False)[:10]
        return {
            'notifications_non_lues': qs,
            'nb_notifications_non_lues': request.user.notifications.filter(lue=False).count(),
        }
    return {}


def theme_utilisateur(request):
    """Injecte la préférence de thème du compte connecté dans tous les
    templates, sans jamais planter si l'objet n'existe pas encore (get_or_create)."""
    if request.user.is_authenticated:
        preference, _ = PreferenceUtilisateur.objects.get_or_create(utilisateur=request.user)
        return {'theme_utilisateur': preference.theme}
    return {'theme_utilisateur': 'auto'}
