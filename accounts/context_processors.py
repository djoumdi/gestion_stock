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
    """Injecte le thème du compte connecté dans tous les templates. Le thème est
    gardé en cache par utilisateur et invalidé à chaque sauvegarde de la
    préférence (voir PreferenceUtilisateur.save)."""
    from django.core.cache import cache
    if not request.user.is_authenticated:
        return {'theme_utilisateur': 'auto'}

    cle = f'theme_utilisateur_{request.user.pk}'
    theme = cache.get(cle)
    if theme is None:
        preference, _ = PreferenceUtilisateur.objects.get_or_create(utilisateur=request.user)
        theme = preference.theme
        cache.set(cle, theme, 3600)
    return {'theme_utilisateur': theme}
