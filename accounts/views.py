# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def liste_notifications(request):
    notifications = request.user.notifications.all()[:50]
    request.user.notifications.filter(lue=False).update(lue=True)
    return render(request, 'notifications.html', {'notifications': notifications})
