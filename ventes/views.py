from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from .models import Vente, LigneVente, Facture, Paiement
from clients.models import Client
from stock.models import Produit


@login_required
@permission_required('ventes.view_vente', raise_exception=True)
def liste_ventes(request):
    peut_tout_voir = request.user.is_superuser or request.user.groups.filter(
        name__in=['Administrateur', 'Responsable']
    ).exists()

    if peut_tout_voir:
        ventes = Vente.objects.all().order_by('-date_vente')
    else:
        ventes = Vente.objects.filter(vendeur=request.user).order_by('-date_vente')

    return render(request, 'ventes/liste_ventes.html', {'ventes': ventes})


@login_required
@permission_required('ventes.add_vente', raise_exception=True)
def nouvelle_vente(request):
    produits = Produit.objects.all()
    clients = Client.objects.all()

    if request.method == 'POST':
        client_id = request.POST.get('client')
        nouveau_nom = request.POST.get('nouveau_client_nom', '').strip()

        if nouveau_nom:
            client = Client.objects.create(
                nom=nouveau_nom,
                telephone=request.POST.get('nouveau_client_telephone', ''),
                email=request.POST.get('nouveau_client_email', '')
            )
        elif client_id:
            client = get_object_or_404(Client, id=client_id)
        else:
            client = None

        vente = Vente.objects.create(client=client, vendeur=request.user)

        produit_ids = request.POST.getlist('produit')
        quantites = request.POST.getlist('quantite')

        for produit_id, quantite in zip(produit_ids, quantites):
            if produit_id and quantite:
                produit = get_object_or_404(Produit, id=produit_id)
                LigneVente.objects.create(
                    vente=vente,
                    produit=produit,
                    quantite=int(quantite),
                    prix_unitaire=produit.prix_vente
                )

        Facture.objects.create(vente=vente)
        return redirect('ventes:detail_vente', pk=vente.pk)

    return render(request, 'ventes/nouvelle_vente.html', {'produits': produits, 'clients': clients})


@login_required
@permission_required('ventes.view_vente', raise_exception=True)
def detail_vente(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    facture, _ = Facture.objects.get_or_create(vente=vente)
    return render(request, 'ventes/detail_vente.html', {'vente': vente, 'facture': facture})


@login_required
@permission_required('ventes.view_vente', raise_exception=True)
def facture_vente(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    facture, _ = Facture.objects.get_or_create(vente=vente)
    return render(request, 'ventes/facture_vente.html', {'vente': vente, 'facture': facture})


@login_required
@permission_required('ventes.add_paiement', raise_exception=True)
def enregistrer_paiement(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    facture, _ = Facture.objects.get_or_create(vente=vente)

    if hasattr(facture, 'paiement'):
        return redirect('ventes:detail_vente', pk=vente.pk)

    if request.method == 'POST':
        Paiement.objects.create(
            facture=facture,
            montant=request.POST.get('montant') or vente.total,
            mode_paiement=request.POST.get('mode_paiement', Paiement.ESPECES),
        )
    return redirect('ventes:detail_vente', pk=vente.pk)
