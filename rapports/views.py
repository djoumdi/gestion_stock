from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.utils import timezone
from datetime import timedelta
from stock.models import Produit, MouvementStock
from ventes.models import Vente, LigneVente
from achats.models import Achat


def _est_dans_groupe(utilisateur, nom_groupe):
    return utilisateur.groups.filter(name=nom_groupe).exists()


from django.db.models.functions import TruncDate


def total_des_ventes(queryset_ventes):
    """Montant total d'un ensemble de ventes en UNE seule requête."""
    return LigneVente.objects.filter(vente__in=queryset_ventes).aggregate(
        total=Sum(F('quantite') * F('prix_unitaire'))
    )['total'] or 0


def labels_des_jours(debut, fin):
    return [(debut + timedelta(days=i)).strftime('%d/%m') for i in range((fin - debut).days + 1)]


def totaux_par_jour(queryset, champ_date, debut, fin, expression_total):
    """Totaux par jour sur une période, en UNE requête groupée (au lieu d'une
    requête par jour)."""
    lignes = (
        queryset.filter(**{f'{champ_date}__date__range': (debut, fin)})
        .annotate(jour=TruncDate(champ_date))
        .order_by()
        .values('jour')
        .annotate(total=Sum(expression_total))
    )
    par_jour = {ligne['jour']: float(ligne['total'] or 0) for ligne in lignes}
    return [par_jour.get(debut + timedelta(days=i), 0.0) for i in range((fin - debut).days + 1)]


@login_required
def tableau_de_bord(request):
    utilisateur = request.user
    aujourdhui = timezone.localdate()
    debut_mois = aujourdhui.replace(day=1)

    est_admin = utilisateur.is_superuser or _est_dans_groupe(utilisateur, 'Administrateur')
    est_gestionnaire = _est_dans_groupe(utilisateur, 'Gestionnaire de stock')
    est_magasinier = _est_dans_groupe(utilisateur, 'Magasinier') and not est_admin and not est_gestionnaire
    est_caissier = _est_dans_groupe(utilisateur, 'Caissier') and not est_admin and not est_gestionnaire and not est_magasinier

    context = {'utilisateur': utilisateur}

    # --- Compte sans rôle assigné : page d'accueil neutre, jamais de 403 ---
    if not (est_admin or est_gestionnaire or est_magasinier or est_caissier):
        context['role_dashboard'] = 'aucun_role'
        return render(request, 'rapports/tableau_de_bord.html', context)

    # --- Vue Caissier : centrée sur SES ventes personnelles ---
    if est_caissier:
        mes_ventes_jour = Vente.objects.filter(vendeur=utilisateur, date_vente__date=aujourdhui)
        mes_ventes_mois = Vente.objects.filter(vendeur=utilisateur, date_vente__date__gte=debut_mois)

        debut_semaine = aujourdhui - timedelta(days=6)
        labels_jours = labels_des_jours(debut_semaine, aujourdhui)
        mes_totaux_jours = totaux_par_jour(
            Vente.objects.filter(vendeur=utilisateur), 'date_vente', debut_semaine, aujourdhui,
            F('lignes__quantite') * F('lignes__prix_unitaire'))

        context.update({
            'role_dashboard': 'vendeur',
            'mes_ventes_jour_montant': total_des_ventes(mes_ventes_jour),
            'mes_ventes_jour_nombre': mes_ventes_jour.count(),
            'mes_ventes_mois_montant': total_des_ventes(mes_ventes_mois),
            'mes_ventes_mois_nombre': mes_ventes_mois.count(),
            'mes_dernieres_ventes': Vente.objects.filter(vendeur=utilisateur).order_by('-date_vente')[:8],
            'produits_en_rupture': Produit.objects.filter(quantite_stock=0).order_by('nom')[:8],
            'labels_jours': labels_jours,
            'mes_totaux_jours': mes_totaux_jours,
        })
        return render(request, 'rapports/tableau_de_bord.html', context)

    # --- Vue Magasinier : centrée sur les réceptions à faire et les mouvements de stock ---
    if est_magasinier:
        achats_a_receptionner = Achat.objects.filter(
            statut__in=[Achat.EN_ATTENTE, Achat.COMMANDE]
        ).select_related('fournisseur').order_by('-date_achat')

        debut_semaine = aujourdhui - timedelta(days=6)
        labels_jours = labels_des_jours(debut_semaine, aujourdhui)
        mouvements_semaine = (
            MouvementStock.objects.filter(date__date__range=(debut_semaine, aujourdhui))
            .annotate(jour=TruncDate('date'))
            .order_by()
            .values('jour', 'type_mouvement')
            .annotate(q=Sum('quantite'))
        )
        par_jour_type = {(m['jour'], m['type_mouvement']): m['q'] or 0 for m in mouvements_semaine}
        jours = [debut_semaine + timedelta(days=i) for i in range(7)]
        entrees_jours = [par_jour_type.get((j, MouvementStock.ENTREE), 0) for j in jours]
        sorties_jours = [par_jour_type.get((j, MouvementStock.SORTIE), 0) for j in jours]

        context.update({
            'role_dashboard': 'magasinier',
            'achats_a_receptionner': achats_a_receptionner[:8],
            'nb_achats_a_receptionner': achats_a_receptionner.count(),
            'derniers_mouvements': MouvementStock.objects.select_related('produit').order_by('-date')[:8],
            'produits_en_rupture': Produit.objects.filter(quantite_stock=0).order_by('nom')[:8],
            'labels_jours': labels_jours,
            'entrees_jours': entrees_jours,
            'sorties_jours': sorties_jours,
        })
        return render(request, 'rapports/tableau_de_bord.html', context)

    # --- Vue Gestionnaire de stock : centrée sur le stock et les achats ---
    if est_gestionnaire:
        produits_en_alerte = Produit.objects.filter(quantite_stock__lte=F('seuil_alerte'))
        achats_en_attente = Achat.objects.filter(
            statut__in=[Achat.EN_ATTENTE, Achat.COMMANDE]
        ).select_related('fournisseur').order_by('-date_achat')

        valeur_stock = Produit.objects.aggregate(
            valeur=Sum(F('quantite_stock') * F('prix_vente'))
        )['valeur'] or 0

        debut_semaine = aujourdhui - timedelta(days=6)
        labels_jours = labels_des_jours(debut_semaine, aujourdhui)
        achats_totaux_jours = totaux_par_jour(
            Achat.objects.all(), 'date_achat', debut_semaine, aujourdhui,
            F('lignes__quantite') * F('lignes__prix_unitaire'))

        context.update({
            'role_dashboard': 'gestionnaire',
            'valeur_stock': valeur_stock,
            'produits_en_alerte': produits_en_alerte,
            'achats_en_attente': achats_en_attente[:8],
            'nb_achats_en_attente': achats_en_attente.count(),
            'derniers_mouvements': MouvementStock.objects.select_related('produit').order_by('-date')[:8],
            'labels_jours': labels_jours,
            'achats_totaux_jours': achats_totaux_jours,
        })
        return render(request, 'rapports/tableau_de_bord.html', context)

    # --- Vue Administrateur : vue d'ensemble complète du magasin ---
    ventes_du_jour = Vente.objects.filter(date_vente__date=aujourdhui)
    total_ventes_jour = total_des_ventes(ventes_du_jour)

    valeur_stock = Produit.objects.aggregate(
        valeur=Sum(F('quantite_stock') * F('prix_vente'))
    )['valeur'] or 0

    produits_en_alerte = Produit.objects.filter(quantite_stock__lte=F('seuil_alerte'))
    nb_ventes_mois = Vente.objects.filter(date_vente__date__gte=debut_mois).count()

    debut_semaine = aujourdhui - timedelta(days=6)
    labels_jours = labels_des_jours(debut_semaine, aujourdhui)
    totaux_jours = totaux_par_jour(
        Vente.objects.all(), 'date_vente', debut_semaine, aujourdhui,
        F('lignes__quantite') * F('lignes__prix_unitaire'))

    # --- Ventes par catégorie (top 5) ---
    categories_stats = (
        LigneVente.objects.values('produit__categorie__nom')
        .annotate(total_ventes=Sum(F('quantite') * F('prix_unitaire')))
        .order_by('-total_ventes')[:5]
    )
    categories_labels = [
        item['produit__categorie__nom'] if item['produit__categorie__nom'] else 'Sans catégorie'
        for item in categories_stats
    ]
    categories_data = [float(item['total_ventes'] or 0) for item in categories_stats]

    dernieres_ventes = Vente.objects.all().order_by('-date_vente')[:5]

    context.update({
        'role_dashboard': 'admin',
        'total_ventes_jour': total_ventes_jour,
        'valeur_stock': valeur_stock,
        'produits_en_alerte': produits_en_alerte,
        'nb_ventes_mois': nb_ventes_mois,
        'labels_jours': labels_jours,
        'totaux_jours': totaux_jours,
        'categories_labels': categories_labels,
        'categories_data': categories_data,
        'dernieres_ventes': dernieres_ventes,
        'achats_en_attente_nombre': Achat.objects.filter(statut__in=[Achat.EN_ATTENTE, Achat.COMMANDE]).count(),
    })
    return render(request, 'rapports/tableau_de_bord.html', context)