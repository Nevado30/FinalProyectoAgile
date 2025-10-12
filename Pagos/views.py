from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import Pago

def pagos_pendientes(request):
    pagos = (Pago.objects
                  .select_related('prestamo', 'prestamo__persona')
                  .filter(estado='Pendiente')
                  .order_by('fecha_vencimiento', 'prestamo__persona__apellidos', 'numero_cuota'))
    return render(request, 'pagos/pendientes.html', {'pagos': pagos})

def pagos_vencidos(request):
    hoy = date.today()
    pagos = (Pago.objects
                  .select_related('prestamo', 'prestamo__persona')
                  .filter(estado__in=['Pendiente', 'Vencido'], fecha_vencimiento__lt=hoy)
                  .order_by('fecha_vencimiento'))
    # marcar como 'Vencido' visualmente (sin modificar DB)
    return render(request, 'pagos/vencidos.html', {'pagos': pagos, 'hoy': hoy})

@require_POST
def marcar_pagado(request, pago_id):
    pago = get_object_or_404(Pago, pk=pago_id)
    pago.estado = 'Pagado'
    from datetime import date as _d
    pago.fecha_pago = _d.today()
    pago.save()
    # volver a la página anterior (si viene ?next=)
    next_url = request.POST.get('next') or reverse('pagos:pendientes')
    return redirect(next_url)

def lista_pagos(request):
    pagos = (Pago.objects
                  .select_related('prestamo', 'prestamo__persona')
                  .order_by('fecha_vencimiento', 'numero_cuota'))
    return render(request, 'pagos/lista_pagos.html', {'pagos': pagos})