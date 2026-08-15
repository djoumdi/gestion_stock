from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .models import ParametresMagasin
from accounts.notifications import enregistrer_action


@login_required
@permission_required('parametres.change_parametresmagasin', raise_exception=True)
def parametres(request):
    config = ParametresMagasin.charger()

    if request.method == 'POST':
        config.nom_magasin = request.POST.get('nom_magasin', '').strip() or config.nom_magasin
        config.adresse = request.POST.get('adresse', '').strip()
        config.telephone = request.POST.get('telephone', '').strip()
        config.email = request.POST.get('email', '').strip()
        config.devise = request.POST.get('devise', '').strip() or 'FCFA'
        config.unite_mesure_defaut = request.POST.get('unite_mesure_defaut', '').strip()

        try:
            config.taux_tva = request.POST.get('taux_tva') or 0
        except (TypeError, ValueError):
            config.taux_tva = 0

        if request.FILES.get('logo'):
            config.logo = request.FILES['logo']

        config.save()
        enregistrer_action(request.user, "a modifié les paramètres du magasin")
        messages.success(request, "Paramètres enregistrés.")
        return redirect('parametres:parametres')

    return render(request, 'parametres/parametres.html', {'config': config})
