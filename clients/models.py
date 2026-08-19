# clients/models.py
from django.db import models


class Client(models.Model):
    nom = models.CharField(max_length=200, db_index=True)
    telephone = models.CharField(max_length=20, blank=True, db_index=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.nom
