from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import ProtectedError
from django.utils import timezone
from django.http import FileResponse
from .models import Produit, Categorie, Marque, MouvementStock, Inventaire, LigneInventaire
from .import_export import exporter_produits_xlsx, importer_produits_xlsx
from fournisseurs.models import Fournisseur
from accounts.notifications import notifier_utilisateur, notifier_administrateurs, enregistrer_action


@login_required
@permission_required('stock.view_produit', raise_exception=True)
def liste_produits(request):
    produits = Produit.objects.all().order_by('nom')
    categories = Categorie.objects.all().order_by('nom')
    return render(request, 'stock/liste_produits.html', {'produits': produits, 'categories': categories})


@login_required
@permission_required('stock.view_produit', raise_exception=True)
def exporter_produits(request):
    produits = Produit.objects.select_related('marque', 'categorie', 'fournisseur').order_by('nom')
    buffer = exporter_produits_xlsx(produits)
    return FileResponse(buffer, as_attachment=True, filename='produits.xlsx')


@login_required
@permission_required('stock.add_produit', raise_exception=True)
@permission_required('stock.change_produit', raise_exception=True)
def importer_produits(request):
    if request.method == 'POST':
        fichier = request.FILES.get('fichier')
        if not fichier:
            messages.error(request, "Sélectionnez un fichier .xlsx à importer.")
            return redirect('stock:importer_produits')

        if not fichier.name.lower().endswith('.xlsx'):
            messages.error(request, "Le fichier doit être au format .xlsx (utilisez l'export comme modèle).")
            return redirect('stock:importer_produits')

        resultat = importer_produits_xlsx(fichier, Produit, Marque, Categorie, Fournisseur)

        if resultat.crees or resultat.modifies:
            enregistrer_action(
                request.user,
                f"a importé un fichier produits ({resultat.crees} créé(s), {resultat.modifies} modifié(s))",
            )
            messages.success(
                request,
                f"Import terminé : {resultat.crees} produit(s) créé(s), {resultat.modifies} mis à jour."
            )
        if resultat.erreurs:
            for erreur in resultat.erreurs[:20]:
                messages.warning(request, erreur)
            if len(resultat.erreurs) > 20:
                messages.warning(request, f"... et {len(resultat.erreurs) - 20} autre(s) ligne(s) en erreur.")

        return redirect('stock:liste_produits')

    return render(request, 'stock/importer_produits.html')


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
            reference=request.POST.get('reference', '').strip(),
            code_barres=request.POST.get('code_barres', '').strip(),
            description=request.POST.get('description', '').strip(),
            marque_id=marque_id if marque_id else None,
            categorie_id=categorie_id if categorie_id else None,
            fournisseur_id=fournisseur_id if fournisseur_id else None,
            prix_achat=request.POST.get('prix_achat'),
            prix_vente=request.POST.get('prix_vente'),
            seuil_alerte=request.POST.get('seuil_alerte') or 5,
            seuil_max=request.POST.get('seuil_max') or None,
        )
        # quantite_stock reste à 0 (valeur par défaut du modèle) : on ne la
        # fixe jamais directement. Un stock de départ éventuel passe par un
        # MouvementStock ENTREE, comme n'importe quel autre mouvement — c'est
        # ce qui garantit que quantite_stock == somme des mouvements à tout moment.
        if request.FILES.get('image'):
            produit.image = request.FILES['image']
            produit.save()

        quantite_initiale = int(request.POST.get('quantite_stock') or 0)
        if quantite_initiale > 0:
            MouvementStock.objects.create(
                produit=produit,
                type_mouvement=MouvementStock.ENTREE,
                quantite=quantite_initiale,
                motif="Stock initial à la création du produit",
            )

        enregistrer_action(request.user, f"a ajouté le produit « {produit.nom} »", lien=f"/produits/{produit.pk}/")

        return redirect('stock:detail_produit', pk=produit.pk)

    return render(request, 'stock/ajouter_produit.html', {
        'marques': Marque.objects.all(),
        'categories': Categorie.objects.all(),
        'fournisseurs': Fournisseur.objects.filter(actif=True),
    })


@login_required
@permission_required('stock.view_produit', raise_exception=True)
def detail_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == 'POST':
        if not request.user.has_perm('stock.change_produit'):
            messages.error(request, "Tu n'as pas le droit de modifier ce produit.")
            return redirect('stock:detail_produit', pk=produit.pk)

        produit.nom = request.POST.get('nom')
        reference = request.POST.get('reference', '').strip()
        if reference:
            produit.reference = reference
        produit.code_barres = request.POST.get('code_barres', '').strip()
        produit.description = request.POST.get('description', '').strip()
        marque_id = request.POST.get('marque')
        produit.marque_id = marque_id if marque_id else None
        produit.prix_achat = request.POST.get('prix_achat')
        produit.prix_vente = request.POST.get('prix_vente')
        produit.seuil_alerte = request.POST.get('seuil_alerte')
        produit.seuil_max = request.POST.get('seuil_max') or None
        if request.FILES.get('image'):
            produit.image = request.FILES['image']
        produit.save()
        return redirect('stock:detail_produit', pk=produit.pk)

    return render(request, 'stock/detail_produit.html', {
        'produit': produit,
        'marques': Marque.objects.all(),
    })


@login_required
@permission_required('stock.delete_produit', raise_exception=True)
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == 'POST':
        nom = produit.nom
        try:
            produit.delete()
        except ProtectedError:
            messages.error(
                request,
                f"Impossible de supprimer « {nom} » : il est référencé dans des ventes, achats ou inventaires existants."
            )
            return redirect('stock:detail_produit', pk=pk)

        enregistrer_action(request.user, f"a supprimé le produit « {nom} »")
        messages.success(request, f"Produit « {nom} » supprimé.")
        return redirect('stock:liste_produits')

    return redirect('stock:detail_produit', pk=pk)


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
@permission_required('stock.view_mouvementstock', raise_exception=True)
def historique_mouvements(request):
    mouvements = MouvementStock.objects.select_related('produit').order_by('-date')

    produit_id = request.GET.get('produit')
    if produit_id:
        mouvements = mouvements.filter(produit_id=produit_id)

    type_mouvement = request.GET.get('type')
    if type_mouvement in (MouvementStock.ENTREE, MouvementStock.SORTIE):
        mouvements = mouvements.filter(type_mouvement=type_mouvement)

    date_debut = request.GET.get('date_debut')
    if date_debut:
        mouvements = mouvements.filter(date__date__gte=date_debut)

    date_fin = request.GET.get('date_fin')
    if date_fin:
        mouvements = mouvements.filter(date__date__lte=date_fin)

    from django.core.paginator import Paginator
    pagination = Paginator(mouvements, 50)
    page = pagination.get_page(request.GET.get('page'))

    return render(request, 'stock/historique_mouvements.html', {
        'page_obj': page,
        'produits': Produit.objects.all().order_by('nom'),
        'produit_selectionne': produit_id or '',
        'type_selectionne': type_mouvement or '',
        'date_debut': date_debut or '',
        'date_fin': date_fin or '',
    })


@login_required
@permission_required('stock.add_mouvementstock', raise_exception=True)
def nouveau_mouvement(request):
    if request.method == 'POST':
        produit = get_object_or_404(Produit, pk=request.POST.get('produit'))
        type_mouvement = request.POST.get('type_mouvement')
        motif = request.POST.get('motif', '').strip()

        if type_mouvement not in (MouvementStock.ENTREE, MouvementStock.SORTIE):
            messages.error(request, "Type de mouvement invalide.")
            return redirect('stock:nouveau_mouvement')

        try:
            quantite = int(request.POST.get('quantite') or 0)
        except ValueError:
            quantite = 0

        if quantite <= 0:
            messages.error(request, "La quantité doit être supérieure à zéro.")
            return redirect('stock:nouveau_mouvement')

        if not motif:
            messages.error(request, "Indique un motif (perte, casse, correction d'inventaire...).")
            return redirect('stock:nouveau_mouvement')

        if type_mouvement == MouvementStock.SORTIE and quantite > produit.quantite_stock:
            messages.error(
                request,
                f"Stock insuffisant : « {produit.nom} » n'a que {produit.quantite_stock} en stock, "
                f"impossible de sortir {quantite}."
            )
            return redirect('stock:nouveau_mouvement')

        MouvementStock.objects.create(
            produit=produit,
            type_mouvement=type_mouvement,
            quantite=quantite,
            motif=motif,
        )

        enregistrer_action(
            request.user,
            f"a saisi un mouvement manuel ({'entrée' if type_mouvement == MouvementStock.ENTREE else 'sortie'} de {quantite}) sur « {produit.nom} » — motif : {motif}",
            lien=f"/produits/mouvements/",
        )
        messages.success(request, f"Mouvement enregistré : {produit.nom} — {quantite} unité(s).")
        return redirect('stock:historique_mouvements')

    return render(request, 'stock/nouveau_mouvement.html', {
        'produits': Produit.objects.all().order_by('nom'),
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

        enregistrer_action(request.user, f"a créé l'inventaire #{inventaire.id}", lien=f"/produits/inventaires/{inventaire.pk}/")

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
            enregistrer_action(request.user, f"a validé l'inventaire #{inventaire.id} (ajustements de stock appliqués)", lien=lien)

            messages.success(request, f"Inventaire #{inventaire.id} validé — les écarts ont été appliqués au stock.")
            return redirect('stock:detail_inventaire', pk=inventaire.pk)

    return render(request, 'stock/detail_inventaire.html', {'inventaire': inventaire})
