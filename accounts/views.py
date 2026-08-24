# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import JsonResponse
from .models import HistoriqueAction, PreferenceUtilisateur
from .notifications import enregistrer_action


@login_required
def liste_notifications(request):
    notifications = request.user.notifications.all()[:50]
    request.user.notifications.filter(lue=False).update(lue=True)
    return render(request, 'notifications.html', {'notifications': notifications})


@login_required
@permission_required('accounts.view_historiqueaction', raise_exception=True)
def liste_historique(request):
    actions = HistoriqueAction.objects.select_related('utilisateur').all()[:200]
    return render(request, 'historique.html', {'actions': actions})


@login_required
@permission_required('auth.view_user', raise_exception=True)
def liste_utilisateurs(request):
    utilisateurs = User.objects.all().order_by('username').prefetch_related('groups')
    return render(request, 'utilisateurs/liste_utilisateurs.html', {'utilisateurs': utilisateurs})


@login_required
@permission_required('auth.add_user', raise_exception=True)
def ajouter_utilisateur(request):
    groupes = Group.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        groupe_id = request.POST.get('groupe')
        mot_de_passe = request.POST.get('password', '')

        if not username or not mot_de_passe:
            messages.error(request, "Le nom d'utilisateur et le mot de passe sont obligatoires.")
            return render(request, 'utilisateurs/ajouter_utilisateur.html', {'groupes': groupes})

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Le nom d'utilisateur « {username} » est déjà pris.")
            return render(request, 'utilisateurs/ajouter_utilisateur.html', {'groupes': groupes})

        try:
            validate_password(mot_de_passe)
        except ValidationError as erreurs:
            for erreur in erreurs:
                messages.error(request, erreur)
            return render(request, 'utilisateurs/ajouter_utilisateur.html', {'groupes': groupes})

        utilisateur = User.objects.create_user(
            username=username, email=email, password=mot_de_passe,
            first_name=first_name, last_name=last_name,
        )

        if groupe_id:
            groupe = get_object_or_404(Group, pk=groupe_id)
            utilisateur.groups.add(groupe)

        enregistrer_action(request.user, f"a créé le compte utilisateur « {utilisateur.username} »")
        messages.success(request, f"Compte « {utilisateur.username} » créé avec succès.")
        return redirect('accounts:detail_utilisateur', pk=utilisateur.pk)

    return render(request, 'utilisateurs/ajouter_utilisateur.html', {'groupes': groupes})


@login_required
@permission_required('auth.change_user', raise_exception=True)
def detail_utilisateur(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    groupes = Group.objects.all()
    groupe_actuel = utilisateur.groups.first()

    if request.method == 'POST':
        action = request.POST.get('action', 'modifier')

        if action == 'modifier':
            utilisateur.email = request.POST.get('email', '').strip()
            utilisateur.first_name = request.POST.get('first_name', '').strip()
            utilisateur.last_name = request.POST.get('last_name', '').strip()

            groupe_id = request.POST.get('groupe')
            utilisateur.groups.clear()
            if groupe_id:
                groupe = get_object_or_404(Group, pk=groupe_id)
                utilisateur.groups.add(groupe)

            utilisateur.save()
            enregistrer_action(request.user, f"a modifié le compte utilisateur « {utilisateur.username} »")
            messages.success(request, "Compte mis à jour.")
            return redirect('accounts:detail_utilisateur', pk=utilisateur.pk)

        elif action == 'basculer_actif':
            if utilisateur == request.user:
                messages.error(request, "Tu ne peux pas désactiver ton propre compte.")
            else:
                utilisateur.is_active = not utilisateur.is_active
                utilisateur.save()
                statut = "réactivé" if utilisateur.is_active else "désactivé"
                enregistrer_action(request.user, f"a {statut} le compte utilisateur « {utilisateur.username} »")
                messages.success(request, f"Compte « {utilisateur.username} » {statut}.")
            return redirect('accounts:detail_utilisateur', pk=utilisateur.pk)

        elif action == 'reinitialiser_mot_de_passe':
            nouveau_mot_de_passe = request.POST.get('nouveau_mot_de_passe', '')
            try:
                validate_password(nouveau_mot_de_passe, user=utilisateur)
            except ValidationError as erreurs:
                for erreur in erreurs:
                    messages.error(request, erreur)
                return redirect('accounts:detail_utilisateur', pk=utilisateur.pk)

            utilisateur.set_password(nouveau_mot_de_passe)
            utilisateur.save()
            enregistrer_action(request.user, f"a réinitialisé le mot de passe du compte « {utilisateur.username} »")
            messages.success(request, f"Mot de passe de « {utilisateur.username} » réinitialisé.")
            return redirect('accounts:detail_utilisateur', pk=utilisateur.pk)

    return render(request, 'utilisateurs/detail_utilisateur.html', {
        'utilisateur': utilisateur,
        'groupes': groupes,
        'groupe_actuel': groupe_actuel,
    })


@login_required
def mon_compte(request):
    """Espace personnel de CHAQUE utilisateur connecté (pas une page admin) :
    infos personnelles, mot de passe, thème. Pas de @permission_required au-delà
    de @login_required — gérer ses propres infos ne demande aucune permission
    particulière, juste d'être connecté."""
    preference, _ = PreferenceUtilisateur.objects.get_or_create(utilisateur=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'profil':
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.email = request.POST.get('email', '').strip()
            request.user.save()
            enregistrer_action(request.user, "a mis à jour ses informations personnelles")
            messages.success(request, "Informations personnelles mises à jour.")
            return redirect('accounts:mon_compte')

        elif action == 'mot_de_passe':
            ancien_mot_de_passe = request.POST.get('ancien_mot_de_passe', '')
            nouveau_mot_de_passe = request.POST.get('nouveau_mot_de_passe', '')
            confirmation = request.POST.get('confirmation_mot_de_passe', '')

            if not request.user.check_password(ancien_mot_de_passe):
                messages.error(request, "Mot de passe actuel incorrect.")
                return redirect('accounts:mon_compte')

            if nouveau_mot_de_passe != confirmation:
                messages.error(request, "Les deux mots de passe saisis ne correspondent pas.")
                return redirect('accounts:mon_compte')

            try:
                validate_password(nouveau_mot_de_passe, user=request.user)
            except ValidationError as erreurs:
                for erreur in erreurs:
                    messages.error(request, erreur)
                return redirect('accounts:mon_compte')

            request.user.set_password(nouveau_mot_de_passe)
            request.user.save()
            # ESSENTIEL : sans ça, changer son propre mot de passe invalide la
            # session en cours et déconnecte immédiatement l'utilisateur, ce
            # qui donnerait l'impression que l'action a échoué.
            update_session_auth_hash(request, request.user)
            enregistrer_action(request.user, "a changé son mot de passe")
            messages.success(request, "Mot de passe modifié avec succès.")
            return redirect('accounts:mon_compte')

        elif action == 'theme':
            theme = request.POST.get('theme')
            if theme in dict(PreferenceUtilisateur.THEME_CHOICES):
                preference.theme = theme
                preference.save()
                messages.success(request, "Thème mis à jour.")
            return redirect('accounts:mon_compte')

    return render(request, 'mon_compte.html', {'preference': preference})


@login_required
def definir_theme(request):
    """Endpoint léger appelé en arrière-plan (fetch) par le bouton de bascule
    rapide clair/sombre dans la barre du haut, pour persister le choix sans
    recharger la page. Le même réglage reste modifiable via un vrai formulaire
    sur la page Mon compte, pour les gens sans JavaScript."""
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)

    theme = request.POST.get('theme')
    if theme not in dict(PreferenceUtilisateur.THEME_CHOICES):
        return JsonResponse({'ok': False, 'erreur': 'theme invalide'}, status=400)

    preference, _ = PreferenceUtilisateur.objects.get_or_create(utilisateur=request.user)
    preference.theme = theme
    preference.save()
    return JsonResponse({'ok': True})
