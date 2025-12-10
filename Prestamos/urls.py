from django.urls import path
from . import views

app_name = 'prestamos'

urlpatterns = [
    path('', views.lista_prestamos, name='lista'),
    path('<int:prestamo_id>/pagos/', views.pagos_por_prestamo, name='pagos_por_prestamo'),
    path('nuevo/', views.crear_prestamo, name='crear'),
    path('<int:prestamo_id>/editar/', views.editar_prestamo, name='editar'),
    path('<int:prestamo_id>/eliminar/', views.eliminar_prestamo, name='eliminar'),
    path('acreedores/', views.lista_acreedores, name='acreedores_lista'),
    path('acreedores/nuevo/', views.crear_acreedor, name='acreedor_nuevo'),
    path('acreedores/<int:acreedor_id>/editar/', views.editar_acreedor, name='acreedor_editar'),
    path('acreedores/<int:acreedor_id>/eliminar/', views.eliminar_acreedor, name='acreedor_eliminar'),
]
