import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('achats', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='achat',
            name='token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
