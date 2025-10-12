from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/reportes/', permanent=False)),
    path('personas/', include('Persona.urls')),
    path('prestamos/', include('Prestamos.urls')),
    path('pagos/', include('Pagos.urls')),
    path('reportes/', include('Reportes.urls')),
    path('seguridad/', include('Seguridad.urls')),
]
