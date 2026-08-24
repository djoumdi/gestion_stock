# commandes/views.py
from functools import wraps
from django.contrib.auth import login as django_login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import CompteClient, CommandeClient, LigneCommandeClient
from clients.models import Client
from stock.models import Produit, MouvementStock
from ventes.models import Vente, LigneVente, Facture
from accounts.notifications import enregistrer_action


def client_requis(vue):
    """Comme @login_required, mais exige en plus un CompteClient — empêche
    un membre du staff (Administrateur, Caissier...) d'atterrir par erreur
    sur les pages du portail, et vice-versa."""
    @wraps(vue)
    @login_required
    def enveloppe(request, *args, **kwargs):
        if not hasattr(request.user, 'compte_client'):
            messages.error(request, "Cette page est réservée aux clients du portail.")
            return redirect('rapports:tableau_de_bord')
        return vue(request, *args, **kwargs)
    return enveloppe


# ==================== INSCRIPTION / CONNEXION ====================

def inscription(request):
    if request.user.is_authenticated:
        return redirect('commandes:catalogue' if hasattr(request.user, 'compte_client') else 'rapports:tableau_de_bord')

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        email = request.POST.get('email', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        mot_de_passe = request.POST.get('password', '')

        erreurs = []
        if not nom:
            erreurs.append("Le nom est obligatoire.")
        if not email:
            erreurs.append("L'email est obligatoire.")
        elif User.objects.filter(username=email).exists():
            erreurs.append("Un compte existe déjà avec cet email.")

        if not erreurs:
            try:
                validate_password(mot_de_passe)
            except ValidationError as liste_erreurs:
                erreurs.extend(liste_erreurs)

        if erreurs:
            for erreur in erreurs:
                messages.error(request, erreur)
            return render(request, 'commandes/inscription.html', {
                'nom': nom, 'email': email, 'telephone': telephone,
            })

        with transaction.atomic():
            utilisateur = User.objects.create_user(username=email, email=email, password=mot_de_passe)
            client = Client.objects.create(nom=nom, email=email, telephone=telephone)
            CompteClient.objects.create(utilisateur=utilisateur, client=client)

        django_login(request, utilisateur)
        messages.success(request, f"Bienvenue {nom} ! Ton compte a été créé.")
        return redirect('commandes:catalogue')

    return render(request, 'commandes/inscription.html')


# ==================== CATALOGUE & COMMANDE ====================

@client_requis
def catalogue(request):
    produits = Produit.objects.select_related('categorie', 'marque').filter(quantite_stock__gt=0).order_by('nom')

    recherche = request.GET.get('q', '').strip()
    if recherche:
        produits = produits.filter(nom__icontains=recherche)

    return render(request, 'commandes/catalogue.html', {'produits': produits, 'recherche': recherche})


@client_requis
def passer_commande(request):
    if request.method != 'POST':
        return redirect('commandes:catalogue')

    client = request.user.compte_client.client
    adresse = request.POST.get('adresse_livraison', '').strip()
    telephone = request.POST.get('telephone_contact', '').strip()
    notes = request.POST.get('notes_client', '').strip()

    if not adresse:
        messages.error(request, "Indique une adresse de livraison.")
        return redirect('commandes:catalogue')

    produit_ids = request.POST.getlist('produit')
    quantites = request.POST.getlist('quantite')

    lignes_demandees = []
    for produit_id, quantite in zip(produit_ids, quantites):
        if not produit_id or not quantite:
            continue
        try:
            quantite = int(quantite)
        except ValueError:
            continue
        if quantite <= 0:
            continue
        produit = get_object_or_404(Produit, id=produit_id)
        lignes_demandees.append((produit, quantite))

    if not lignes_demandees:
        messages.error(request, "Ton panier est vide.")
        return redirect('commandes:catalogue')

    with transaction.atomic():
        commande = CommandeClient.objects.create(
            client=client,
            adresse_livraison=adresse,
            telephone_contact=telephone or client.telephone,
            notes_client=notes,
        )
        for produit, quantite in lignes_demandees:
            LigneCommandeClient.objects.create(
                commande=commande, produit=produit, quantite=quantite, prix_unitaire=produit.prix_vente,
            )

    messages.success(request, f"Commande {commande.code} envoyée ! Tu seras notifié dès qu'elle sera prise en charge.")
    return redirect('commandes:detail_commande', pk=commande.pk)


@client_requis
def mes_commandes(request):
    commandes = CommandeClient.objects.filter(client=request.user.compte_client.client).order_by('-date_commande')
    return render(request, 'commandes/mes_commandes.html', {'commandes': commandes})


@client_requis
def detail_commande(request, pk):
    commande = get_object_or_404(CommandeClient, pk=pk, client=request.user.compte_client.client)

    if request.method == 'POST' and request.POST.get('action') == 'valider_livraison':
        if commande.statut != CommandeClient.LIVREE:
            messages.error(request, "Cette commande n'est pas encore marquée comme livrée.")
            return redirect('commandes:detail_commande', pk=pk)

        if request.FILES.get('photo_livraison'):
            commande.photo_livraison = request.FILES['photo_livraison']
        if request.FILES.get('video_livraison'):
            commande.video_livraison = request.FILES['video_livraison']

        commande.statut = CommandeClient.VALIDEE
        commande.date_validation = timezone.now()
        commande.save()

        enregistrer_action(request.user, f"a validé la réception de la commande {commande.code}")
        messages.success(request, "Merci ! La livraison est confirmée.")
        return redirect('commandes:detail_commande', pk=pk)

    return render(request, 'commandes/detail_commande.html', {'commande': commande})


# ==================== GESTION STAFF (Gestionnaire de stock, Caissier, Administrateur) ====================

@login_required
@permission_required('commandes.view_commandeclient', raise_exception=True)
def liste_commandes_client(request):
    commandes = CommandeClient.objects.select_related('client', 'livreur').exclude(
        statut=CommandeClient.VALIDEE
    ).order_by('-date_commande')
    return render(request, 'commandes/staff_liste_commandes.html', {'commandes': commandes})


@login_required
@permission_required('commandes.view_commandeclient', raise_exception=True)
def staff_detail_commande(request, pk):
    commande = get_object_or_404(CommandeClient, pk=pk)
    livreurs = User.objects.filter(groups__name='Livreur', is_active=True)

    if request.method == 'POST':
        if not request.user.has_perm('commandes.change_commandeclient'):
            messages.error(request, "Tu n'as pas le droit de modifier cette commande.")
            return redirect('commandes:staff_detail_commande', pk=pk)

        action = request.POST.get('action')

        if action == 'confirmer':
            if commande.statut != CommandeClient.EN_ATTENTE:
                messages.error(request, "Cette commande a déjà été traitée.")
                return redirect('commandes:staff_detail_commande', pk=pk)

            lignes = list(commande.lignes.select_related('produit').all())
            produits_insuffisants = [
                f"{ligne.produit.nom} (demandé {ligne.quantite}, disponible {ligne.produit.quantite_stock})"
                for ligne in lignes if ligne.quantite > ligne.produit.quantite_stock
            ]
            if produits_insuffisants:
                messages.error(request, "Stock insuffisant pour : " + ", ".join(produits_insuffisants))
                return redirect('commandes:staff_detail_commande', pk=pk)

            with transaction.atomic():
                vente = Vente.objects.create(client=commande.client, vendeur=request.user)
                for ligne in lignes:
                    LigneVente.objects.create(
                        vente=vente, produit=ligne.produit, quantite=ligne.quantite, prix_unitaire=ligne.prix_unitaire,
                    )
                    MouvementStock.objects.create(
                        produit=ligne.produit, type_mouvement=MouvementStock.SORTIE,
                        quantite=ligne.quantite, motif=f"Commande portail {commande.code}",
                    )
                Facture.objects.create(vente=vente)

                commande.vente = vente
                commande.statut = CommandeClient.CONFIRMEE
                commande.date_confirmation = timezone.now()
                commande.save()

            enregistrer_action(request.user, f"a confirmé la commande client {commande.code} (vente {vente.code} créée)")
            messages.success(request, f"Commande confirmée — {vente.code} créée et stock mis à jour.")

        elif action == 'assigner_livreur':
            livreur_id = request.POST.get('livreur')
            if commande.statut not in (CommandeClient.CONFIRMEE, CommandeClient.ASSIGNEE):
                messages.error(request, "Confirme d'abord la commande avant d'assigner un livreur.")
                return redirect('commandes:staff_detail_commande', pk=pk)
            if not livreur_id:
                messages.error(request, "Choisis un livreur.")
                return redirect('commandes:staff_detail_commande', pk=pk)

            commande.livreur = get_object_or_404(User, pk=livreur_id)
            commande.statut = CommandeClient.ASSIGNEE
            commande.date_assignation = timezone.now()
            commande.save()

            enregistrer_action(request.user, f"a assigné la commande {commande.code} au livreur {commande.livreur.username}")
            messages.success(request, f"Commande assignée à {commande.livreur.username}.")

        elif action == 'annuler':
            if commande.statut in (CommandeClient.LIVREE, CommandeClient.VALIDEE):
                messages.error(request, "Impossible d'annuler une commande déjà livrée.")
                return redirect('commandes:staff_detail_commande', pk=pk)

            # Si le stock avait déjà été décrémenté (commande confirmée), on le restitue.
            if commande.statut in (CommandeClient.CONFIRMEE, CommandeClient.ASSIGNEE, CommandeClient.EN_LIVRAISON):
                with transaction.atomic():
                    for ligne in commande.lignes.select_related('produit').all():
                        MouvementStock.objects.create(
                            produit=ligne.produit, type_mouvement=MouvementStock.ENTREE,
                            quantite=ligne.quantite, motif=f"Annulation commande portail {commande.code}",
                        )
                    commande.statut = CommandeClient.ANNULEE
                    commande.save()
            else:
                commande.statut = CommandeClient.ANNULEE
                commande.save()

            enregistrer_action(request.user, f"a annulé la commande client {commande.code}")
            messages.success(request, "Commande annulée.")

        return redirect('commandes:staff_detail_commande', pk=pk)

    return render(request, 'commandes/staff_detail_commande.html', {'commande': commande, 'livreurs': livreurs})


# ==================== ESPACE LIVREUR ====================

@login_required
@permission_required('commandes.view_commandeclient', raise_exception=True)
def mes_livraisons(request):
    commandes = CommandeClient.objects.select_related('client').filter(
        livreur=request.user, statut__in=[CommandeClient.ASSIGNEE, CommandeClient.EN_LIVRAISON],
    ).order_by('date_assignation')
    return render(request, 'commandes/mes_livraisons.html', {'commandes': commandes})


@login_required
@permission_required('commandes.change_commandeclient', raise_exception=True)
def changer_statut_livraison(request, pk):
    commande = get_object_or_404(CommandeClient, pk=pk, livreur=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'demarrer' and commande.statut == CommandeClient.ASSIGNEE:
            commande.statut = CommandeClient.EN_LIVRAISON
            commande.save()
            messages.success(request, "Livraison démarrée.")

        elif action == 'livree' and commande.statut == CommandeClient.EN_LIVRAISON:
            commande.statut = CommandeClient.LIVREE
            commande.date_livraison = timezone.now()
            commande.save()
            enregistrer_action(request.user, f"a marqué la commande {commande.code} comme livrée")
            messages.success(request, "Commande marquée comme livrée. En attente de confirmation du client.")

    return redirect('commandes:mes_livraisons')
