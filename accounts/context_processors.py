# accounts/context_processors.py
def notifications(request):
    if request.user.is_authenticated:
        qs = request.user.notifications.filter(lue=False)[:10]
        return {
            'notifications_non_lues': qs,
            'nb_notifications_non_lues': request.user.notifications.filter(lue=False).count(),
        }
    return {}
