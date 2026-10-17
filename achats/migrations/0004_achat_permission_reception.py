from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('achats', '0003_ajouter_index_performance'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='achat',
            options={'permissions': [('receptionner_achat', 'Peut réceptionner une commande (mise à jour du stock)')]},
        ),
    ]
