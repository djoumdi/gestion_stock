from django.urls import path
from . import views

app_name = 'achats'

urlpatterns = [
    path('', views.liste_achats, name='liste_achats'),
    path('nouveau/', views.nouvel_achat, name='nouvel_achat'),
    path('<int:pk>/', views.detail_achat, name='detail_achat'),
    path('<int:pk>/valider-reception/', views.valider_reception, name='valider_reception'),
    path('<int:pk>/modifier-statut/', views.modifier_statut_achat, name='modifier_statut_achat'),
]
