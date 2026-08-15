from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.utils import timezone
from datetime import timedelta
from stock.models import Produit, MouvementStock
from ventes.models import Vente
from achats.models import Achat


def _est_dans_groupe(utilisateur, nom_groupe):
    return utilisateur.groups.filter(name=nom_groupe).exists()


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

        context.update({
            'role_dashboard': 'vendeur',
            'mes_ventes_jour_montant': sum(v.total for v in mes_ventes_jour),
            'mes_ventes_jour_nombre': mes_ventes_jour.count(),
            'mes_ventes_mois_montant': sum(v.total for v in mes_ventes_mois),
            'mes_ventes_mois_nombre': mes_ventes_mois.count(),
            'mes_dernieres_ventes': Vente.objects.filter(vendeur=utilisateur).order_by('-date_vente')[:8],
            'produits_en_rupture': Produit.objects.filter(quantite_stock=0).order_by('nom')[:8],
        })
        return render(request, 'rapports/tableau_de_bord.html', context)

    # --- Vue Magasinier : centrée sur les réceptions à faire et les mouvements de stock ---
    if est_magasinier:
        achats_a_receptionner = Achat.objects.filter(
            statut__in=[Achat.EN_ATTENTE, Achat.COMMANDE]
        ).select_related('fournisseur').order_by('-date_achat')

        context.update({
            'role_dashboard': 'magasinier',
            'achats_a_receptionner': achats_a_receptionner[:8],
            'nb_achats_a_receptionner': achats_a_receptionner.count(),
            'derniers_mouvements': MouvementStock.objects.select_related('produit').order_by('-date')[:8],
            'produits_en_rupture': Produit.objects.filter(quantite_stock=0).order_by('nom')[:8],
        })
        return render(request, 'rapports/tableau_de_bord.html', context)

    # --- Vue Gestionnaire de stock : centrée sur le stock et les achats ---
    if est_gestionnaire:
        produits_en_alerte = [p for p in Produit.objects.all() if p.en_alerte]
        achats_en_attente = Achat.objects.filter(
            statut__in=[Achat.EN_ATTENTE, Achat.COMMANDE]
        ).select_related('fournisseur').order_by('-date_achat')

        valeur_stock = Produit.objects.aggregate(
            valeur=Sum(F('quantite_stock') * F('prix_vente'))
        )['valeur'] or 0

        context.update({
            'role_dashboard': 'gestionnaire',
            'valeur_stock': valeur_stock,
            'produits_en_alerte': produits_en_alerte,
            'achats_en_attente': achats_en_attente[:8],
            'nb_achats_en_attente': achats_en_attente.count(),
            'derniers_mouvements': MouvementStock.objects.select_related('produit').order_by('-date')[:8],
        })
        return render(request, 'rapports/tableau_de_bord.html', context)

    # --- Vue Administrateur : vue d'ensemble complète du magasin ---
    ventes_du_jour = Vente.objects.filter(date_vente__date=aujourdhui)
    total_ventes_jour = sum(v.total for v in ventes_du_jour)

    valeur_stock = Produit.objects.aggregate(
        valeur=Sum(F('quantite_stock') * F('prix_vente'))
    )['valeur'] or 0

    produits_en_alerte = [p for p in Produit.objects.all() if p.en_alerte]
    nb_ventes_mois = Vente.objects.filter(date_vente__date__gte=debut_mois).count()

    labels_jours = []
    totaux_jours = []
    for i in range(6, -1, -1):
        jour = aujourdhui - timedelta(days=i)
        ventes_ce_jour = Vente.objects.filter(date_vente__date=jour)
        total_jour = sum(v.total for v in ventes_ce_jour)
        labels_jours.append(jour.strftime('%d/%m'))
        totaux_jours.append(float(total_jour))

    dernieres_ventes = Vente.objects.all().order_by('-date_vente')[:5]

    context.update({
        'role_dashboard': 'admin',
        'total_ventes_jour': total_ventes_jour,
        'valeur_stock': valeur_stock,
        'produits_en_alerte': produits_en_alerte,
        'nb_ventes_mois': nb_ventes_mois,
        'labels_jours': labels_jours,
        'totaux_jours': totaux_jours,
        'dernieres_ventes': dernieres_ventes,
        'achats_en_attente_nombre': Achat.objects.filter(statut__in=[Achat.EN_ATTENTE, Achat.COMMANDE]).count(),
    })
    return render(request, 'rapports/tableau_de_bord.html', context)
