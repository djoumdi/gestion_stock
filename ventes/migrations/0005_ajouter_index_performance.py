from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0004_devis_retours'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vente',
            name='date_vente',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
