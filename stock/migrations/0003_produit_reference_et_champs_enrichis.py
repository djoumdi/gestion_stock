from django.db import migrations, models


def generer_references_existantes(apps, schema_editor):
    """Les produits déjà en base n'ont pas de référence : on leur en génère
    une avant d'activer la contrainte unique sur ce champ (impossible
    d'ajouter une contrainte unique directement sur une colonne où toutes
    les valeurs existantes seraient une chaîne vide identique)."""
    Produit = apps.get_model('stock', 'Produit')
    for produit in Produit.objects.filter(reference=''):
        produit.reference = f"PRD-{produit.pk:06d}"
        produit.save(update_fields=['reference'])


def ne_rien_faire(apps, schema_editor):
    """Pas de retour en arrière utile ici : rendre la référence vide en
    revenant sur cette migration recréerait le même conflit d'unicité."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0002_inventaire_ligneinventaire'),
    ]

    operations = [
        migrations.AddField(
            model_name='produit',
            name='reference',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='produit',
            name='code_barres',
            field=models.CharField(blank=True, default='', max_length=50, help_text="Code EAN/UPC scanné ou saisi manuellement. Optionnel."),
        ),
        migrations.AddField(
            model_name='produit',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='produit',
            name='seuil_max',
            field=models.PositiveIntegerField(blank=True, null=True, help_text="Seuil de stock MAXIMUM recommandé (optionnel)."),
        ),
        migrations.AlterField(
            model_name='produit',
            name='seuil_alerte',
            field=models.PositiveIntegerField(default=5, help_text="Seuil de stock MINIMUM avant alerte."),
        ),
        migrations.RunPython(generer_references_existantes, ne_rien_faire),
        migrations.AlterField(
            model_name='produit',
            name='reference',
            field=models.CharField(blank=True, max_length=50, unique=True),
        ),
    ]
