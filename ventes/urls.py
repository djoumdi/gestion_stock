from django.urls import path
from . import views

app_name = 'ventes'

urlpatterns = [
    path('', views.liste_ventes, name='liste_ventes'),
    path('nouvelle/', views.nouvelle_vente, name='nouvelle_vente'),
    path('<int:pk>/', views.detail_vente, name='detail_vente'),
    path('<int:pk>/facture/', views.facture_vente, name='facture_vente'),
    path('<int:pk>/facture/pdf/', views.facture_pdf, name='facture_pdf'),
    path('facture/<uuid:token>/', views.facture_publique, name='facture_publique'),
    path('facture/<uuid:token>/pdf/', views.facture_pdf_publique, name='facture_pdf_publique'),
    path('<int:pk>/payer/', views.enregistrer_paiement, name='enregistrer_paiement'),

    # Devis
    path('devis/', views.liste_devis, name='liste_devis'),
    path('devis/nouveau/', views.nouveau_devis, name='nouveau_devis'),
    path('devis/<int:pk>/', views.detail_devis, name='detail_devis'),
    path('devis/<int:pk>/statut/', views.changer_statut_devis, name='changer_statut_devis'),
    path('devis/<int:pk>/convertir/', views.convertir_devis, name='convertir_devis'),
    path('devis/<int:pk>/pdf/', views.devis_pdf, name='devis_pdf'),
    path('devis/pdf/<uuid:token>/', views.devis_pdf_publique, name='devis_pdf_publique'),

    # Retours / Avoirs
    path('<int:vente_pk>/retour/nouveau/', views.nouveau_retour, name='nouveau_retour'),
    path('retours/<int:pk>/', views.detail_retour, name='detail_retour'),
    path('retours/<int:pk>/pdf/', views.avoir_pdf, name='avoir_pdf'),
    path('retours/pdf/<uuid:token>/', views.avoir_pdf_publique, name='avoir_pdf_publique'),
]
