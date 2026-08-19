from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='nom',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='client',
            name='telephone',
            field=models.CharField(blank=True, db_index=True, max_length=20),
        ),
    ]
