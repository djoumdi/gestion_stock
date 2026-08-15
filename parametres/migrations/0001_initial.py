import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ParametresMagasin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_magasin', models.CharField(default='TechStock', max_length=150)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='parametres/')),
                ('adresse', models.CharField(blank=True, max_length=255)),
                ('telephone', models.CharField(blank=True, max_length=30)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('devise', models.CharField(default='FCFA', max_length=10)),
                ('taux_tva', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('unite_mesure_defaut', models.CharField(blank=True, default='unité', max_length=30)),
            ],
            options={
                'verbose_name': 'Paramètres du magasin',
                'verbose_name_plural': 'Paramètres du magasin',
            },
        ),
    ]
