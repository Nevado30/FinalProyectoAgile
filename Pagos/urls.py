from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    path('', views.lista_pagos, name='lista_pagos'),
    path('pendientes/', views.pagos_pendientes, name='pendientes'),
    path('vencidos/', views.pagos_vencidos, name='vencidos'),
    path('pagar/<int:pago_id>/', views.marcar_pagado, name='marcar_pagado'),
]
