# baseParcial/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/personas/', permanent=False)),  # raíz → personas
    path('personas/', include('Persona.urls')),
    path('prestamos/', include('Prestamos.urls')),
    path('pagos/', include('Pagos.urls')),
]
