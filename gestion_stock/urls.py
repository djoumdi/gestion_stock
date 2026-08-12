from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('rapports.urls')),
    path('produits/', include('stock.urls')),
    path('fournisseurs/', include('fournisseurs.urls')),
    path('clients/', include('clients.urls')),
    path('achats/', include('achats.urls')),
    path('ventes/', include('ventes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
