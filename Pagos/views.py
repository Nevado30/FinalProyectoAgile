from django.shortcuts import render
from .models import Pago

def lista_pagos(request):
    pagos = Pago.objects.select_related('prestamo', 'prestamo__persona').order_by('fecha_vencimiento', 'numero_cuota')
    return render(request, 'pagos/lista_pagos.html', {'pagos': pagos})
