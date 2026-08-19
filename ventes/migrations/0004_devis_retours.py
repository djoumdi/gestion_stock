import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0003_facture_token'),
        ('clients', '0001_initial'),
        ('stock', '0003_produit_reference_et_champs_enrichis'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Devis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_validite', models.DateField(blank=True, help_text="Date jusqu'à laquelle le devis est valable. Optionnel.", null=True)),
                ('statut', models.CharField(choices=[('EN_ATTENTE', 'En attente'), ('ACCEPTE', 'Accepté'), ('REFUSE', 'Refusé'), ('CONVERTI', 'Converti en vente')], default='EN_ATTENTE', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('client', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='devis', to='clients.client')),
                ('vendeur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='devis_crees', to=settings.AUTH_USER_MODEL)),
                ('vente', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='devis_origine', to='ventes.vente')),
            ],
            options={'ordering': ['-date_creation']},
        ),
        migrations.CreateModel(
            name='LigneDevis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite', models.PositiveIntegerField(validators=[MinValueValidator(1)])),
                ('prix_unitaire', models.DecimalField(decimal_places=2, max_digits=10)),
                ('devis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='ventes.devis')),
                ('produit', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='stock.produit')),
            ],
        ),
        migrations.CreateModel(
            name='Retour',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motif', models.TextField()),
                ('date_retour', models.DateTimeField(auto_now_add=True)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('cree_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='retours_crees', to=settings.AUTH_USER_MODEL)),
                ('vente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='retours', to='ventes.vente')),
            ],
            options={'ordering': ['-date_retour']},
        ),
        migrations.CreateModel(
            name='LigneRetour',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite', models.PositiveIntegerField(validators=[MinValueValidator(1)])),
                ('ligne_vente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='retours', to='ventes.lignevente')),
                ('retour', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='ventes.retour')),
            ],
        ),
    ]
