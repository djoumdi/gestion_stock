import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0002_ajouter_index_performance'),
        ('ventes', '0006_alter_devis_id_alter_lignedevis_id_and_more'),
        ('stock', '0005_alter_produit_description_alter_produit_image_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompteClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('client', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='compte_client', to='clients.client')),
                ('utilisateur', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='compte_client', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CommandeClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('statut', models.CharField(choices=[
                    ('EN_ATTENTE', 'En attente de confirmation'),
                    ('CONFIRMEE', 'Confirmée'),
                    ('ASSIGNEE', 'Assignée à un livreur'),
                    ('EN_LIVRAISON', 'En livraison'),
                    ('LIVREE', 'Livrée — en attente de validation client'),
                    ('VALIDEE', 'Validée par le client'),
                    ('ANNULEE', 'Annulée'),
                ], default='EN_ATTENTE', max_length=20)),
                ('adresse_livraison', models.CharField(max_length=255)),
                ('telephone_contact', models.CharField(blank=True, max_length=20)),
                ('notes_client', models.TextField(blank=True)),
                ('date_commande', models.DateTimeField(auto_now_add=True)),
                ('date_confirmation', models.DateTimeField(blank=True, null=True)),
                ('date_assignation', models.DateTimeField(blank=True, null=True)),
                ('date_livraison', models.DateTimeField(blank=True, null=True)),
                ('date_validation', models.DateTimeField(blank=True, null=True)),
                ('photo_livraison', models.ImageField(blank=True, null=True, upload_to='livraisons/')),
                ('video_livraison', models.FileField(blank=True, null=True, upload_to='livraisons/')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='commandes_portail', to='clients.client')),
                ('livreur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='livraisons_assignees', to=settings.AUTH_USER_MODEL)),
                ('vente', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='commande_portail', to='ventes.vente')),
            ],
            options={
                'ordering': ['-date_commande'],
            },
        ),
        migrations.CreateModel(
            name='LigneCommandeClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite', models.PositiveIntegerField()),
                ('prix_unitaire', models.DecimalField(decimal_places=2, max_digits=10)),
                ('commande', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='commandes.commandeclient')),
                ('produit', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='stock.produit')),
            ],
        ),
    ]
