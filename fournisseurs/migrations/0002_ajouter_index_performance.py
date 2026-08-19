from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fournisseurs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fournisseur',
            name='nom',
            field=models.CharField(db_index=True, max_length=200),
        ),
    ]
