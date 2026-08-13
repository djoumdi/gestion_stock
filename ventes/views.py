from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from .models import Vente, LigneVente, Facture, Paiement
from clients.models import Client
from stock.models import Produit, MouvementStock


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

        produit_ids = request.POST.getlist('produit')
        quantites = request.POST.getlist('quantite')

        lignes_demandees = []
        for produit_id, quantite in zip(produit_ids, quantites):
            if produit_id and quantite:
                try:
                    quantite = int(quantite)
                except ValueError:
                    continue
                if quantite <= 0:
                    continue
                produit = get_object_or_404(Produit, id=produit_id)
                lignes_demandees.append((produit, quantite))

        if not lignes_demandees:
            messages.error(request, "Veuillez sélectionner au moins un produit avec une quantité valide.")
            return redirect('ventes:nouvelle_vente')

        # On vérifie la disponibilité AVANT de créer quoi que ce soit, pour ne jamais
        # laisser une vente à moitié enregistrée ni faire passer le stock en négatif.
        # Si un même produit est ajouté sur plusieurs lignes, on cumule les quantités demandées.
        quantites_cumulees = {}
        for produit, quantite in lignes_demandees:
            quantites_cumulees[produit.pk] = quantites_cumulees.get(produit.pk, 0) + quantite

        produits_insuffisants = []
        for produit_id, quantite_totale in quantites_cumulees.items():
            produit = next(p for p, _ in lignes_demandees if p.pk == produit_id)
            if quantite_totale > produit.quantite_stock:
                produits_insuffisants.append(f"{produit.nom} (demandé {quantite_totale}, disponible {produit.quantite_stock})")

        if produits_insuffisants:
            messages.error(request, "Stock insuffisant pour : " + ", ".join(produits_insuffisants))
            return redirect('ventes:nouvelle_vente')

        with transaction.atomic():
            vente = Vente.objects.create(client=client, vendeur=request.user)

            for produit, quantite in lignes_demandees:
                LigneVente.objects.create(
                    vente=vente,
                    produit=produit,
                    quantite=quantite,
                    prix_unitaire=produit.prix_vente
                )
                MouvementStock.objects.create(
                    produit=produit,
                    type_mouvement=MouvementStock.SORTIE,
                    quantite=quantite,
                    motif=f"Vente {vente.code}",
                )

            Facture.objects.create(vente=vente)

        messages.success(request, f"{vente.code} enregistrée avec succès.")
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
