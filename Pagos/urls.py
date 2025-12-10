from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    path('', views.lista_pagos, name='lista_pagos'),
    path('pendientes/', views.pagos_pendientes, name='pendientes'),
    path('vencidos/', views.pagos_vencidos, name='vencidos'),
    path("pagar/<int:pago_id>/", views.pagar_cuota, name="pagar_cuota"),
    path("mp/success/", views.mp_success, name="mp_success"),
    path("mp/failure/", views.mp_failure, name="mp_failure"),
    path("mp/pending/", views.mp_pending, name="mp_pending"),
]
