from django.contrib import admin
from django.urls import path, include
from .views import home_redirect

urlpatterns = [
    # Raíz: decide a dónde ir según autenticación
    path('', home_redirect, name='home'),

    # Apps
    path('seguridad/', include('Seguridad.urls')),
    path('personas/', include('Persona.urls')),
    path('prestamos/', include('Prestamos.urls')),
    path('pagos/', include('Pagos.urls')),
    path('reportes/', include('Reportes.urls')),

    # Admin de Django
    path('admin/', admin.site.urls),
]
