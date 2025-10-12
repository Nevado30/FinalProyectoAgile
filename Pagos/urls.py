from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    path('', views.lista_pagos, name='lista'),
    path('pendientes/', views.pagos_pendientes, name='pendientes'),
    path('vencidos/', views.pagos_vencidos, name='vencidos'),
    path('<int:pago_id>/marcar-pagado/', views.marcar_pagado, name='marcar_pagado'),
]
