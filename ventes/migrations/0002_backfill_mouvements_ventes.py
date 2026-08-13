# ventes/migrations/0002_backfill_mouvements_ventes.py
from django.db import migrations


def creer_mouvements_retroactifs(apps, schema_editor):
    """Avant ce correctif, une vente décrémentait le stock directement dans
    LigneVente.save() sans jamais créer de MouvementStock : ces ventes-là sont
    donc invisibles dans l'historique des mouvements.

    On comble le trou pour la traçabilité, MAIS il ne faut surtout pas que
    cette création redécrémente le stock une deuxième fois : le stock a déjà
    été baissé au moment de la vente d'origine. C'est pour ça qu'on utilise
    bulk_create() ici plutôt que MouvementStock.objects.create() — bulk_create
    n'appelle pas save() sur chaque instance, donc l'effet de bord qui ajuste
    produit.quantite_stock (utile pour les NOUVEAUX mouvements) ne se déclenche
    pas ici. Résultat : un historique complet, un stock inchangé.
    """
    LigneVente = apps.get_model('ventes', 'LigneVente')
    MouvementStock = apps.get_model('stock', 'MouvementStock')

    lignes = LigneVente.objects.select_related('vente', 'produit').all()

    nouveaux_mouvements = [
        MouvementStock(
            produit_id=ligne.produit_id,
            type_mouvement='sortie',
            quantite=ligne.quantite,
            motif=f"Vente VTE-{ligne.vente_id:06d} (mouvement reconstitué rétroactivement)",
            date=ligne.vente.date_vente,
        )
        for ligne in lignes
    ]

    if nouveaux_mouvements:
        # Le champ 'date' est en auto_now_add=True : Django écraserait sinon
        # systématiquement notre date reconstituée par l'heure actuelle, même
        # en bulk_create. On désactive temporairement l'auto_now_add le temps
        # de l'insertion pour conserver la vraie date de la vente d'origine.
        champ_date = MouvementStock._meta.get_field('date')
        champ_date.auto_now_add = False
        try:
            MouvementStock.objects.bulk_create(nouveaux_mouvements)
        finally:
            champ_date.auto_now_add = True


def supprimer_mouvements_retroactifs(apps, schema_editor):
    """Ne supprime QUE les mouvements marqués comme reconstitués par cette
    migration, jamais les mouvements créés normalement depuis."""
    MouvementStock = apps.get_model('stock', 'MouvementStock')
    MouvementStock.objects.filter(motif__endswith="(mouvement reconstitué rétroactivement)").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0001_initial'),
        ('stock', '0002_inventaire_ligneinventaire'),
    ]

    operations = [
        migrations.RunPython(creer_mouvements_retroactifs, supprimer_mouvements_retroactifs),
    ]
