from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from .models import Produit, Categorie, Marque, MouvementStock, Inventaire, LigneInventaire
from fournisseurs.models import Fournisseur
from accounts.notifications import notifier_utilisateur, notifier_administrateurs


@login_required
@permission_required('stock.view_produit', raise_exception=True)
def liste_produits(request):
    produits = Produit.objects.all().order_by('nom')
    categories = Categorie.objects.all().order_by('nom')
    return render(request, 'stock/liste_produits.html', {'produits': produits, 'categories': categories})


@login_required
@permission_required('stock.add_produit', raise_exception=True)
def ajouter_produit(request):
    if request.method == 'POST':
        marque_id = request.POST.get('marque')
        categorie_id = request.POST.get('categorie')
        fournisseur_id = request.POST.get('fournisseur')

        # Création à la volée d'une nouvelle marque, si demandée
        nouvelle_marque = request.POST.get('nouvelle_marque', '').strip()
        if nouvelle_marque:
            marque, _ = Marque.objects.get_or_create(nom=nouvelle_marque)
            marque_id = marque.id

        # Idem pour la catégorie
        nouvelle_categorie = request.POST.get('nouvelle_categorie', '').strip()
        if nouvelle_categorie:
            categorie, _ = Categorie.objects.get_or_create(nom=nouvelle_categorie)
            categorie_id = categorie.id

        produit = Produit.objects.create(
            nom=request.POST.get('nom'),
            marque_id=marque_id if marque_id else None,
            categorie_id=categorie_id if categorie_id else None,
            fournisseur_id=fournisseur_id if fournisseur_id else None,
            prix_achat=request.POST.get('prix_achat'),
            prix_vente=request.POST.get('prix_vente'),
            quantite_stock=request.POST.get('quantite_stock') or 0,
            seuil_alerte=request.POST.get('seuil_alerte') or 5,
        )
        if request.FILES.get('image'):
            produit.image = request.FILES['image']
            produit.save()

        return redirect('stock:detail_produit', pk=produit.pk)

    return render(request, 'stock/ajouter_produit.html', {
        'marques': Marque.objects.all(),
        'categories': Categorie.objects.all(),
        'fournisseurs': Fournisseur.objects.filter(actif=True),
    })


@login_required
@permission_required('stock.change_produit', raise_exception=True)
def detail_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == 'POST':
        produit.nom = request.POST.get('nom')
        marque_id = request.POST.get('marque')
        produit.marque_id = marque_id if marque_id else None
        produit.prix_achat = request.POST.get('prix_achat')
        produit.prix_vente = request.POST.get('prix_vente')
        produit.seuil_alerte = request.POST.get('seuil_alerte')
        if request.FILES.get('image'):
            produit.image = request.FILES['image']
        produit.save()
        return redirect('stock:detail_produit', pk=produit.pk)

    return render(request, 'stock/detail_produit.html', {
        'produit': produit,
        'marques': Marque.objects.all(),
    })


@login_required
@permission_required('stock.add_categorie', raise_exception=True)
def categories_marques(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'ajouter_categorie':
            nom = request.POST.get('nom_categorie', '').strip()
            if nom:
                Categorie.objects.get_or_create(nom=nom)
        elif action == 'supprimer_categorie':
            Categorie.objects.filter(pk=request.POST.get('categorie_id')).delete()
        elif action == 'ajouter_marque':
            nom = request.POST.get('nom_marque', '').strip()
            if nom:
                Marque.objects.get_or_create(nom=nom)
        elif action == 'supprimer_marque':
            Marque.objects.filter(pk=request.POST.get('marque_id')).delete()

        return redirect('stock:categories_marques')

    from django.db.models import Count
    categories = Categorie.objects.annotate(nb_produits=Count('produits'))
    marques = Marque.objects.annotate(nb_produits=Count('produits'))

    return render(request, 'stock/categories_marques.html', {
        'categories': categories,
        'marques': marques,
    })


@login_required
@permission_required('stock.view_inventaire', raise_exception=True)
def liste_inventaires(request):
    inventaires = Inventaire.objects.all().order_by('-date_creation')
    return render(request, 'stock/liste_inventaires.html', {'inventaires': inventaires})


@login_required
@permission_required('stock.add_inventaire', raise_exception=True)
def nouvel_inventaire(request):
    if request.method == 'POST':
        produit_ids = request.POST.getlist('produits')

        if not produit_ids:
            messages.error(request, "Sélectionne au moins un produit à inventorier.")
            return redirect('stock:nouvel_inventaire')

        inventaire = Inventaire.objects.create(cree_par=request.user)

        for produit_id in produit_ids:
            produit = get_object_or_404(Produit, pk=produit_id)
            LigneInventaire.objects.create(
                inventaire=inventaire,
                produit=produit,
                quantite_theorique=produit.quantite_stock,
            )

        messages.success(request, f"Inventaire #{inventaire.id} créé — passe au comptage physique.")
        return redirect('stock:detail_inventaire', pk=inventaire.pk)

    produits = Produit.objects.all().order_by('nom')
    return render(request, 'stock/nouvel_inventaire.html', {'produits': produits})


@login_required
@permission_required('stock.view_inventaire', raise_exception=True)
def detail_inventaire(request, pk):
    inventaire = get_object_or_404(Inventaire, pk=pk)

    if request.method == 'POST' and inventaire.statut == Inventaire.EN_COURS:
        if not request.user.has_perm('stock.change_inventaire'):
            messages.error(request, "Tu n'as pas le droit de modifier cet inventaire.")
            return redirect('stock:detail_inventaire', pk=inventaire.pk)

        action = request.POST.get('action')

        if action == 'enregistrer_comptage':
            for ligne in inventaire.lignes.all():
                valeur = request.POST.get(f'quantite_physique_{ligne.id}')
                if valeur not in (None, ''):
                    ligne.quantite_physique = int(valeur)
                    ligne.save()
            messages.success(request, "Comptage enregistré.")
            return redirect('stock:detail_inventaire', pk=inventaire.pk)

        elif action == 'valider':
            lignes_non_comptees = inventaire.lignes.filter(quantite_physique__isnull=True)
            if lignes_non_comptees.exists():
                messages.error(request, "Toutes les lignes doivent être comptées avant de valider l'inventaire.")
                return redirect('stock:detail_inventaire', pk=inventaire.pk)

            for ligne in inventaire.lignes.all():
                if ligne.ecart and ligne.ecart != 0:
                    MouvementStock.objects.create(
                        produit=ligne.produit,
                        type_mouvement=MouvementStock.ENTREE if ligne.ecart > 0 else MouvementStock.SORTIE,
                        quantite=abs(ligne.ecart),
                        motif=f"Ajustement inventaire #{inventaire.id}",
                    )

            inventaire.statut = Inventaire.VALIDE
            inventaire.date_validation = timezone.now()
            inventaire.save()

            lien = f"/produits/inventaires/{inventaire.pk}/"
            notifier_utilisateur(request.user, f"Vous avez validé l'inventaire #{inventaire.id}.", lien=lien)
            notifier_administrateurs(
                f"{request.user.username} a validé l'inventaire #{inventaire.id} — les stocks ont été ajustés.",
                lien=lien,
                exclure=request.user,
            )

            messages.success(request, f"Inventaire #{inventaire.id} validé — les écarts ont été appliqués au stock.")
            return redirect('stock:detail_inventaire', pk=inventaire.pk)

    return render(request, 'stock/detail_inventaire.html', {'inventaire': inventaire})
