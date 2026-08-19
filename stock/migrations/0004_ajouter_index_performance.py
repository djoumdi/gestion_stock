from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0003_produit_reference_et_champs_enrichis'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produit',
            name='nom',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='produit',
            name='code_barres',
            field=models.CharField(blank=True, db_index=True, max_length=50,
                help_text="Code EAN/UPC scanné ou saisi manuellement. Optionnel."),
        ),
        migrations.AlterField(
            model_name='mouvementstock',
            name='date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
