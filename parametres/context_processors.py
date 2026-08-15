from .models import ParametresMagasin


def config_magasin(request):
    return {'config_magasin': ParametresMagasin.charger()}
