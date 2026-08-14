from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('notifications/', views.liste_notifications, name='notifications'),
    path('historique/', views.liste_historique, name='historique'),
    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateurs/ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),
    path('utilisateurs/<int:pk>/', views.detail_utilisateur, name='detail_utilisateur'),
]
