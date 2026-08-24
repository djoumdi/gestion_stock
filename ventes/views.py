from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.urls import reverse
from django.http import FileResponse
from .models import Vente, LigneVente, Facture, Paiement, Devis, LigneDevis, Retour, LigneRetour
from .pdf import generer_pdf_facture, generer_pdf_devis, generer_pdf_avoir
from clients.models import Client
from stock.models import Produit, MouvementStock
from accounts.notifications import enregistrer_action


@login_required
@permission_required('ventes.view_vente', raise_exception=True)
def liste_ventes(request):
    peut_tout_voir = request.user.is_superuser or request.user.groups.filter(
        name__in=['Administrateur']
    ).exists()

    ventes_qs = Vente.objects.select_related('client', 'vendeur').order_by('-date_vente')
    if not peut_tout_voir:
        ventes_qs = ventes_qs.filter(vendeur=request.user)

    paginator = Paginator(ventes_qs, 30)
    ventes = paginator.get_page(request.GET.get('page'))

    return render(request, 'ventes/liste_ventes.html', {'ventes': ventes})


@login_required
@permission_required('ventes.add_vente', raise_exception=True)
def nouvelle_vente(request):
    produits = Produit.objects.only('id', 'nom', 'prix_vente')
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

        enregistrer_action(request.user, f"a enregistré la vente {vente.code}", lien=f"/ventes/{vente.pk}/")

        messages.success(request, f"{vente.code} enregistrée avec succès.")
        return redirect('ventes:detail_vente', pk=vente.pk)

    return render(request, 'ventes/nouvelle_vente.html', {'produits': produits, 'clients': clients})


@login_required
@permission_required('ventes.view_vente', raise_exception=True)
def detail_vente(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    facture, _ = Facture.objects.get_or_create(vente=vente)

    lien_facture = request.build_absolute_uri(
        reverse('ventes:facture_pdf_publique', args=[facture.token])
    )
    message_whatsapp = (
        f"Bonjour {vente.client.nom if vente.client else ''},\n"
        f"Voici votre facture {facture.numero} d'un montant de {vente.total} FCFA.\n"
        f"Téléchargez le PDF ici : {lien_facture}"
    ).strip()

    return render(request, 'ventes/detail_vente.html', {
        'vente': vente,
        'facture': facture,
        'message_whatsapp': message_whatsapp,
    })


@login_required
@permission_required('ventes.view_vente', raise_exception=True)
def facture_vente(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    facture, _ = Facture.objects.get_or_create(vente=vente)
    return render(request, 'ventes/facture_vente.html', {'vente': vente, 'facture': facture})


def facture_publique(request, token):
    """Page de consultation de facture accessible sans connexion, via un lien
    à usage unique (token opaque) — c'est ce lien qui est envoyé au client par
    WhatsApp. Volontairement pas de @login_required : le client n'a pas de
    compte sur l'application."""
    facture = get_object_or_404(Facture, token=token)
    return render(request, 'ventes/facture_vente.html', {'vente': facture.vente, 'facture': facture})


@login_required
@permission_required('ventes.view_vente', raise_exception=True)
def facture_pdf(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    facture, _ = Facture.objects.get_or_create(vente=vente)
    buffer = generer_pdf_facture(facture)
    return FileResponse(buffer, as_attachment=False, filename=f"{facture.numero}.pdf")


def facture_pdf_publique(request, token):
    """Téléchargement direct du PDF, sans connexion — c'est ce lien-là qu'on
    envoie par WhatsApp (le client récupère un vrai fichier, pas juste une
    page web)."""
    facture = get_object_or_404(Facture, token=token)
    buffer = generer_pdf_facture(facture)
    return FileResponse(buffer, as_attachment=True, filename=f"{facture.numero}.pdf")


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
        enregistrer_action(request.user, f"a enregistré le paiement de la vente {vente.code}", lien=f"/ventes/{vente.pk}/")
    return redirect('ventes:detail_vente', pk=vente.pk)


# ============================= DEVIS =============================

@login_required
@permission_required('ventes.view_devis', raise_exception=True)
def liste_devis(request):
    peut_tout_voir = request.user.is_superuser or request.user.groups.filter(name__in=['Administrateur']).exists()

    if peut_tout_voir:
        devis_qs = Devis.objects.all()
    else:
        devis_qs = Devis.objects.filter(vendeur=request.user)

    return render(request, 'ventes/liste_devis.html', {'liste_devis': devis_qs.select_related('client')})


@login_required
@permission_required('ventes.add_devis', raise_exception=True)
def nouveau_devis(request):
    produits = Produit.objects.only('id', 'nom', 'prix_vente')
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

        lignes_demandees = {}
        for produit_id, quantite in zip(produit_ids, quantites):
            if produit_id and quantite:
                try:
                    quantite = int(quantite)
                except ValueError:
                    continue
                if quantite <= 0:
                    continue
                lignes_demandees[produit_id] = lignes_demandees.get(produit_id, 0) + quantite

        if not lignes_demandees:
            messages.error(request, "Veuillez sélectionner au moins un produit avec une quantité valide.")
            return redirect('ventes:nouveau_devis')

        date_validite = request.POST.get('date_validite') or None

        # Un devis n'engage pas le stock (ce n'est qu'une estimation tant qu'il
        # n'est pas converti) : pas de contrôle de disponibilité ici, contrairement
        # à une vente réelle.
        with transaction.atomic():
            devis = Devis.objects.create(
                client=client, vendeur=request.user,
                date_validite=date_validite,
                notes=request.POST.get('notes', '').strip(),
            )
            for produit_id, quantite in lignes_demandees.items():
                produit = get_object_or_404(Produit, id=produit_id)
                LigneDevis.objects.create(devis=devis, produit=produit, quantite=quantite, prix_unitaire=produit.prix_vente)

        enregistrer_action(request.user, f"a créé le devis {devis.code}", lien=f"/ventes/devis/{devis.pk}/")
        messages.success(request, f"{devis.code} créé avec succès.")
        return redirect('ventes:detail_devis', pk=devis.pk)

    return render(request, 'ventes/nouveau_devis.html', {'produits': produits, 'clients': clients})


@login_required
@permission_required('ventes.view_devis', raise_exception=True)
def detail_devis(request, pk):
    devis = get_object_or_404(Devis, pk=pk)

    lien_devis = request.build_absolute_uri(reverse('ventes:devis_pdf_publique', args=[devis.token]))
    message_whatsapp = (
        f"Bonjour {devis.client.nom if devis.client else ''},\n"
        f"Voici votre devis {devis.code} d'un montant estimé de {devis.total} FCFA"
        + (f", valable jusqu'au {devis.date_validite.strftime('%d/%m/%Y')}" if devis.date_validite else "") + ".\n"
        f"Téléchargez le PDF ici : {lien_devis}"
    ).strip()

    return render(request, 'ventes/detail_devis.html', {
        'devis': devis,
        'message_whatsapp': message_whatsapp,
    })


@login_required
@permission_required('ventes.change_devis', raise_exception=True)
def changer_statut_devis(request, pk):
    devis = get_object_or_404(Devis, pk=pk)

    if request.method == 'POST' and devis.statut in (Devis.EN_ATTENTE,):
        action = request.POST.get('action')
        if action == 'accepter':
            devis.statut = Devis.ACCEPTE
            devis.save()
            enregistrer_action(request.user, f"a marqué le devis {devis.code} comme accepté")
            messages.success(request, f"{devis.code} marqué comme accepté.")
        elif action == 'refuser':
            devis.statut = Devis.REFUSE
            devis.save()
            enregistrer_action(request.user, f"a marqué le devis {devis.code} comme refusé")
            messages.success(request, f"{devis.code} marqué comme refusé.")

    return redirect('ventes:detail_devis', pk=devis.pk)


@login_required
@permission_required('ventes.add_vente', raise_exception=True)
def convertir_devis(request, pk):
    """Transforme un devis accepté en vraie vente : c'est SEULEMENT à ce
    moment que le stock est vérifié et décrémenté — un devis, même accepté,
    n'a jamais réservé de stock."""
    devis = get_object_or_404(Devis, pk=pk)

    if request.method != 'POST' or not devis.est_convertible:
        return redirect('ventes:detail_devis', pk=devis.pk)

    lignes = list(devis.lignes.select_related('produit').all())
    if not lignes:
        messages.error(request, "Ce devis n'a aucune ligne à convertir.")
        return redirect('ventes:detail_devis', pk=devis.pk)

    produits_insuffisants = []
    for ligne in lignes:
        if ligne.quantite > ligne.produit.quantite_stock:
            produits_insuffisants.append(
                f"{ligne.produit.nom} (demandé {ligne.quantite}, disponible {ligne.produit.quantite_stock})"
            )
    if produits_insuffisants:
        messages.error(request, "Conversion impossible, stock insuffisant pour : " + ", ".join(produits_insuffisants))
        return redirect('ventes:detail_devis', pk=devis.pk)

    with transaction.atomic():
        vente = Vente.objects.create(client=devis.client, vendeur=request.user)
        for ligne in lignes:
            LigneVente.objects.create(
                vente=vente, produit=ligne.produit,
                quantite=ligne.quantite, prix_unitaire=ligne.prix_unitaire,
            )
            MouvementStock.objects.create(
                produit=ligne.produit, type_mouvement=MouvementStock.SORTIE,
                quantite=ligne.quantite, motif=f"Vente {vente.code} (converti depuis {devis.code})",
            )
        Facture.objects.create(vente=vente)
        devis.vente = vente
        devis.statut = Devis.CONVERTI
        devis.save()

    enregistrer_action(request.user, f"a converti le devis {devis.code} en vente {vente.code}", lien=f"/ventes/{vente.pk}/")
    messages.success(request, f"{devis.code} converti en {vente.code}.")
    return redirect('ventes:detail_vente', pk=vente.pk)


@login_required
@permission_required('ventes.view_devis', raise_exception=True)
def devis_pdf(request, pk):
    devis = get_object_or_404(Devis, pk=pk)
    buffer = generer_pdf_devis(devis)
    return FileResponse(buffer, as_attachment=False, filename=f"{devis.code}.pdf")


def devis_pdf_publique(request, token):
    devis = get_object_or_404(Devis, token=token)
    buffer = generer_pdf_devis(devis)
    return FileResponse(buffer, as_attachment=True, filename=f"{devis.code}.pdf")


# ============================ RETOURS =============================

@login_required
@permission_required('ventes.add_retour', raise_exception=True)
def nouveau_retour(request, vente_pk):
    vente = get_object_or_404(Vente.objects.prefetch_related('lignes__produit'), pk=vente_pk)
    lignes_retournables = [l for l in vente.lignes.all() if l.quantite_retournable > 0]

    if request.method == 'POST':
        motif = request.POST.get('motif', '').strip()
        if not motif:
            messages.error(request, "Indique un motif pour ce retour.")
            return redirect('ventes:nouveau_retour', vente_pk=vente.pk)

        lignes_a_retourner = []
        for ligne in lignes_retournables:
            valeur = request.POST.get(f'quantite_{ligne.pk}', '').strip()
            if not valeur:
                continue
            try:
                quantite = int(valeur)
            except ValueError:
                continue
            if quantite <= 0:
                continue
            if quantite > ligne.quantite_retournable:
                messages.error(
                    request,
                    f"{ligne.produit.nom} : tu ne peux pas retourner plus de {ligne.quantite_retournable} "
                    f"(déjà {ligne.quantite_deja_retournee} retourné(s) sur {ligne.quantite})."
                )
                return redirect('ventes:nouveau_retour', vente_pk=vente.pk)
            lignes_a_retourner.append((ligne, quantite))

        if not lignes_a_retourner:
            messages.error(request, "Sélectionne au moins un produit à retourner, avec une quantité valide.")
            return redirect('ventes:nouveau_retour', vente_pk=vente.pk)

        with transaction.atomic():
            retour = Retour.objects.create(vente=vente, cree_par=request.user, motif=motif)
            for ligne, quantite in lignes_a_retourner:
                LigneRetour.objects.create(retour=retour, ligne_vente=ligne, quantite=quantite)
                MouvementStock.objects.create(
                    produit=ligne.produit, type_mouvement=MouvementStock.ENTREE,
                    quantite=quantite, motif=f"Retour {retour.code} (vente {vente.code})",
                )

        enregistrer_action(request.user, f"a enregistré le retour {retour.code} sur la vente {vente.code}", lien=f"/ventes/retours/{retour.pk}/")
        messages.success(request, f"{retour.code} enregistré — le stock a été mis à jour.")
        return redirect('ventes:detail_retour', pk=retour.pk)

    return render(request, 'ventes/nouveau_retour.html', {
        'vente': vente,
        'lignes_retournables': lignes_retournables,
    })


@login_required
@permission_required('ventes.view_retour', raise_exception=True)
def detail_retour(request, pk):
    retour = get_object_or_404(Retour.objects.select_related('vente', 'vente__client').prefetch_related('lignes__ligne_vente__produit'), pk=pk)

    lien_avoir = request.build_absolute_uri(reverse('ventes:avoir_pdf_publique', args=[retour.token]))
    message_whatsapp = (
        f"Bonjour {retour.vente.client.nom if retour.vente.client else ''},\n"
        f"Voici votre avoir {retour.code} d'un montant de {retour.total} FCFA, suite au retour sur la vente {retour.vente.code}.\n"
        f"Téléchargez le PDF ici : {lien_avoir}"
    ).strip()

    return render(request, 'ventes/detail_retour.html', {
        'retour': retour,
        'message_whatsapp': message_whatsapp,
    })


@login_required
@permission_required('ventes.view_retour', raise_exception=True)
def avoir_pdf(request, pk):
    retour = get_object_or_404(Retour, pk=pk)
    buffer = generer_pdf_avoir(retour)
    return FileResponse(buffer, as_attachment=False, filename=f"{retour.code}.pdf")


def avoir_pdf_publique(request, token):
    retour = get_object_or_404(Retour, token=token)
    buffer = generer_pdf_avoir(retour)
    return FileResponse(buffer, as_attachment=True, filename=f"{retour.code}.pdf")
