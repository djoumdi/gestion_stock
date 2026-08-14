from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .models import Fournisseur
from accounts.notifications import enregistrer_action


@login_required
@permission_required('fournisseurs.view_fournisseur', raise_exception=True)
def liste_fournisseurs(request):
    fournisseurs = Fournisseur.objects.all().order_by('nom')
    for f in fournisseurs:
        f.nb_produits = f.produits.count()
    return render(request, 'fournisseurs/liste_fournisseurs.html', {'fournisseurs': fournisseurs})


@login_required
@permission_required('fournisseurs.add_fournisseur', raise_exception=True)
def ajouter_fournisseur(request):
    if request.method == 'POST':
        fournisseur = Fournisseur.objects.create(
            nom=request.POST.get('nom'),
            telephone=request.POST.get('telephone'),
            email=request.POST.get('email'),
            adresse=request.POST.get('adresse'),
            ville=request.POST.get('ville'),
        )
        return redirect('fournisseurs:detail_fournisseur', pk=fournisseur.pk)
    return render(request, 'fournisseurs/ajouter_fournisseur.html')


@login_required
@permission_required('fournisseurs.change_fournisseur', raise_exception=True)
def detail_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)

    if request.method == 'POST':
        fournisseur.nom = request.POST.get('nom')
        fournisseur.telephone = request.POST.get('telephone')
        fournisseur.email = request.POST.get('email')
        fournisseur.adresse = request.POST.get('adresse')
        fournisseur.ville = request.POST.get('ville')
        fournisseur.actif = request.POST.get('actif') == 'on'
        fournisseur.save()
        return redirect('fournisseurs:detail_fournisseur', pk=fournisseur.pk)

    produits = fournisseur.produits.all()
    return render(request, 'fournisseurs/detail_fournisseur.html', {'fournisseur': fournisseur, 'produits': produits})


@login_required
@permission_required('fournisseurs.delete_fournisseur', raise_exception=True)
def supprimer_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)

    if request.method == 'POST':
        nom = fournisseur.nom
        fournisseur.delete()
        enregistrer_action(request.user, f"a supprimé le fournisseur « {nom} »")
        messages.success(request, f"Fournisseur « {nom} » supprimé.")
        return redirect('fournisseurs:liste_fournisseurs')

    return redirect('fournisseurs:detail_fournisseur', pk=pk)
