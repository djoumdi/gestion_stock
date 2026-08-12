from django.urls import path
from . import views

app_name = 'ventes'

urlpatterns = [
    path('', views.liste_ventes, name='liste_ventes'),
    path('nouvelle/', views.nouvelle_vente, name='nouvelle_vente'),
    path('<int:pk>/', views.detail_vente, name='detail_vente'),
    path('<int:pk>/facture/', views.facture_vente, name='facture_vente'),
    path('<int:pk>/payer/', views.enregistrer_paiement, name='enregistrer_paiement'),
]
