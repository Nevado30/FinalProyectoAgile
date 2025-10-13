from django.urls import path
from . import views

app_name = 'prestamos'

urlpatterns = [
    path('', views.lista_prestamos, name='lista'),
    path('<int:prestamo_id>/pagos/', views.pagos_por_prestamo, name='pagos_por_prestamo'),
    path('nuevo/', views.crear_prestamo, name='crear'),
]
