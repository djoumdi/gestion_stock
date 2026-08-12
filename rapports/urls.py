from django.urls import path
from . import views

app_name = 'rapports'

urlpatterns = [
    path('', views.tableau_de_bord, name='tableau_de_bord'),
]
