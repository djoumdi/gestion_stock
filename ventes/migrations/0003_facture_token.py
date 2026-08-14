import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ventes', '0002_backfill_mouvements_ventes'),
    ]

    operations = [
        migrations.AddField(
            model_name='facture',
            name='token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
