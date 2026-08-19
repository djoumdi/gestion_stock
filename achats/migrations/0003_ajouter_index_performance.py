from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('achats', '0002_achat_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='achat',
            name='date_achat',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
