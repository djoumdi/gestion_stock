from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_alter_preferenceutilisateur_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='historiqueaction',
            name='type_action',
            field=models.CharField(choices=[('action', 'Action'), ('connexion', 'Connexion')], default='action', max_length=10),
        ),
        migrations.AddField(
            model_name='historiqueaction',
            name='adresse_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
