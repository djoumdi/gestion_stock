# Generated manually to match Django's migration format

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_merge_0005_initial_0006_add_inventaire_permissions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoriqueAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=255)),
                ('lien', models.CharField(blank=True, max_length=255)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('utilisateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions_historique', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': "Action de l'historique",
                'verbose_name_plural': 'Historique des actions',
                'ordering': ['-date'],
            },
        ),
    ]
