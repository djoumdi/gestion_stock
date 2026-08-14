from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import JsonResponse, FileResponse
from django.urls import reverse

from .models import Achat, LigneAchat
from .pdf import generer_pdf_bon_commande
from stock.models import Produit, MouvementStock
from fournisseurs.models import Fournisseur
from accounts.notifications import notifier_utilisateur, notifier_administrateurs, enregistrer_action


@login_required
@permission_required('achats.view_achat', raise_exception=True)
def liste_achats(request):
    achats = Achat.objects.select_related('fournisseur', 'cree_par').all().order_by('-date_achat')
    return render(request, 'achats/liste_achats.html', {'achats': achats})


@login_required
@permission_required('achats.add_achat', raise_exception=True)
def nouvel_achat(request):
    if request.method == 'POST':
        fournisseur_id = request.POST.get('fournisseur')
        notes = request.POST.get('notes', '')

        produits = request.POST.getlist('produits')
        quantites = request.POST.getlist('quantites')
        prix_unitaires = request.POST.getlist('prix_unitaires')

        if not fournisseur_id or not produits:
            messages.error(request, "Veuillez sélectionner un fournisseur et au moins un produit.")
            return redirect('achats:nouvel_achat')

        try:
            with transaction.atomic():
                fournisseur = get_object_or_404(Fournisseur, pk=fournisseur_id)

                achat = Achat.objects.create(
                    fournisseur=fournisseur,
                    cree_par=request.user,
                    notes=notes
                )

                for p_id, qte, prix in zip(produits, quantites, prix_unitaires):
                    if p_id and qte and prix:
                        LigneAchat.objects.create(
                            achat=achat,
                            produit_id=p_id,
                            quantite=int(qte),
                            prix_unitaire=prix
                        )

                lien = reverse('achats:detail_achat', args=[achat.pk])
                notifier_utilisateur(request.user, f"Vous avez créé l'achat {achat.code}.", lien=lien)
                notifier_administrateurs(
                    f"{request.user.username} a créé l'achat {achat.code} ({fournisseur.nom}).",
                    lien=lien,
                    exclure=request.user,
                )
                enregistrer_action(request.user, f"a créé l'achat {achat.code} auprès de {fournisseur.nom}", lien=lien)

                messages.success(request, f"Achat {achat.code} enregistré avec succès.")
                return redirect('achats:detail_achat', pk=achat.pk)

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de l'enregistrement : {e}")
            return redirect('achats:nouvel_achat')

    fournisseurs = Fournisseur.objects.filter(actif=True)
    produits = Produit.objects.all()

    return render(request, 'achats/nouvel_achat.html', {
        'fournisseurs': fournisseurs,
        'produits': produits,
    })


@login_required
@permission_required('achats.view_achat', raise_exception=True)
def detail_achat(request, pk):
    achat = get_object_or_404(Achat.objects.prefetch_related('lignes__produit'), pk=pk)

    lien_bon_commande = request.build_absolute_uri(
        reverse('achats:bon_commande_pdf_public', args=[achat.token])
    )
    message_whatsapp = (
        f"Bonjour {achat.fournisseur.nom if achat.fournisseur else ''},\n"
        f"Voici le bon de commande {achat.code} d'un montant de {achat.total} FCFA.\n"
        f"Téléchargez le PDF ici : {lien_bon_commande}"
    ).strip()

    return render(request, 'achats/detail_achat.html', {
        'achat': achat,
        'message_whatsapp': message_whatsapp,
    })


def bon_commande_public(request, token):
    """Page de consultation du bon de commande accessible sans connexion, via
    un lien à usage unique (token opaque) envoyé au fournisseur par WhatsApp.
    Pas de @login_required : le fournisseur n'a pas de compte sur l'application."""
    achat = get_object_or_404(Achat.objects.prefetch_related('lignes__produit'), token=token)
    return render(request, 'achats/bon_commande.html', {'achat': achat})


@login_required
@permission_required('achats.view_achat', raise_exception=True)
def bon_commande_pdf(request, pk):
    achat = get_object_or_404(Achat.objects.prefetch_related('lignes__produit'), pk=pk)
    buffer = generer_pdf_bon_commande(achat)
    return FileResponse(buffer, as_attachment=False, filename=f"{achat.code}.pdf")


def bon_commande_pdf_public(request, token):
    """Téléchargement direct du PDF, sans connexion — c'est ce lien-là qu'on
    envoie par WhatsApp."""
    achat = get_object_or_404(Achat.objects.prefetch_related('lignes__produit'), token=token)
    buffer = generer_pdf_bon_commande(achat)
    return FileResponse(buffer, as_attachment=True, filename=f"{achat.code}.pdf")


@login_required
@permission_required('achats.change_achat', raise_exception=True)
def valider_reception(request, pk):
    """Valide la réception de la commande : c'est SEULEMENT à ce moment que le stock bouge."""
    achat = get_object_or_404(Achat, pk=pk)

    if achat.statut != Achat.RECU:
        with transaction.atomic():
            for ligne in achat.lignes.select_related('produit'):
                MouvementStock.objects.create(
                    produit=ligne.produit,
                    type_mouvement=MouvementStock.ENTREE,
                    quantite=ligne.quantite,
                    motif=f"Réception achat {achat.code}",
                )
                ligne.produit.prix_achat = ligne.prix_unitaire
                ligne.produit.save()

            achat.statut = Achat.RECU
            achat.save()

            lien = reverse('achats:detail_achat', args=[achat.pk])
            notifier_utilisateur(request.user, f"Vous avez validé la réception de l'achat {achat.code}.", lien=lien)
            notifier_administrateurs(
                f"{request.user.username} a validé la réception de l'achat {achat.code}.",
                lien=lien,
                exclure=request.user,
            )
            enregistrer_action(request.user, f"a validé la réception de l'achat {achat.code} (stock mis à jour)", lien=lien)

            messages.success(request, f"L'achat {achat.code} a été marqué comme reçu et les stocks ont été mis à jour.")

    return redirect('achats:detail_achat', pk=achat.pk)


@login_required
@permission_required('achats.change_achat', raise_exception=True)
def modifier_statut_achat(request, pk):
    """Met à jour le statut d'un achat directement depuis le front-end (AJAX)."""
    if request.method == 'POST':
        achat = get_object_or_404(Achat, pk=pk)
        nouveau_statut = request.POST.get('statut')

        STATUTS_VALIDES = [Achat.EN_ATTENTE, Achat.COMMANDE, Achat.RECU, Achat.ANNULE]

        if nouveau_statut in STATUTS_VALIDES and nouveau_statut != achat.statut:
            with transaction.atomic():
                if nouveau_statut == Achat.RECU and achat.statut != Achat.RECU:
                    for ligne in achat.lignes.select_related('produit'):
                        MouvementStock.objects.create(
                            produit=ligne.produit,
                            type_mouvement=MouvementStock.ENTREE,
                            quantite=ligne.quantite,
                            motif=f"Réception achat {achat.code}",
                        )
                        ligne.produit.prix_achat = ligne.prix_unitaire
                        ligne.produit.save()

                achat.statut = nouveau_statut
                achat.save()

                lien = reverse('achats:detail_achat', args=[achat.pk])
                notifier_utilisateur(request.user, f"Vous avez changé le statut de l'achat {achat.code} en '{achat.get_statut_display()}'.", lien=lien)
                notifier_administrateurs(
                    f"{request.user.username} a changé le statut de l'achat {achat.code} en '{achat.get_statut_display()}'.",
                    lien=lien,
                    exclure=request.user,
                )
                enregistrer_action(request.user, f"a changé le statut de l'achat {achat.code} en « {achat.get_statut_display()} »", lien=lien)

            return JsonResponse({'status': 'success', 'statut': achat.statut})

    return JsonResponse({'status': 'error', 'message': 'Action non autorisée'}, status=400)
