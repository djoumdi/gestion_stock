from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import F, Sum
from django.utils import timezone
from datetime import timedelta
from stock.models import Produit
from ventes.models import Vente


@login_required
@permission_required('stock.view_produit', raise_exception=True)
def tableau_de_bord(request):
    aujourdhui = timezone.localdate()

    ventes_du_jour = Vente.objects.filter(date_vente__date=aujourdhui)
    total_ventes_jour = sum(v.total for v in ventes_du_jour)

    valeur_stock = Produit.objects.aggregate(
        valeur=Sum(F('quantite_stock') * F('prix_vente'))
    )['valeur'] or 0

    produits_en_alerte = [p for p in Produit.objects.all() if p.en_alerte]

    debut_mois = aujourdhui.replace(day=1)
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

    context = {
        'total_ventes_jour': total_ventes_jour,
        'valeur_stock': valeur_stock,
        'produits_en_alerte': produits_en_alerte,
        'nb_ventes_mois': nb_ventes_mois,
        'labels_jours': labels_jours,
        'totaux_jours': totaux_jours,
        'dernieres_ventes': dernieres_ventes,
    }
    return render(request, 'rapports/tableau_de_bord.html', context)
