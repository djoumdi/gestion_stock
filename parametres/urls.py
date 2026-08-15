from django.urls import path
from . import views

app_name = 'parametres'

urlpatterns = [
    path('', views.parametres, name='parametres'),
]
