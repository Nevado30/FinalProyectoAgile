from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'pagos'

urlpatterns = [
    path('',                       login_required(views.lista_pagos),      name='lista'),
    path('pendientes/',            login_required(views.pagos_pendientes), name='pendientes'),
    path('vencidos/',              login_required(views.pagos_vencidos),   name='vencidos'),
    path('<int:pago_id>/marcar-pagado/', login_required(views.marcar_pagado), name='marcar_pagado'),
]
