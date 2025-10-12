from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('personas/', include('Persona.urls')),
    path('prestamos/', include('Prestamos.urls')),
    path('pagos/', include('Pagos.urls')),
]

