from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from .models import Pago
from Moneda.services import convertir_monto, obtener_tipo_cambio

def _fila(pago, a_moneda):
    origen = pago.prestamo.moneda_prestamo or 'PEN'
    monto_base = convertir_monto(pago.monto, origen, a_moneda, pago.fecha_vencimiento)
    # Para un equivalente opcional en otra moneda podrías agregarlo según query param
    return {'pago': pago, 'monto_base': monto_base, 'monto_destino': None}

@login_required
def lista_pagos(request):
    persona = getattr(request.user, 'persona', None)
    base = (persona.moneda_preferida if persona and persona.moneda_preferida else 'PEN').upper()

    qs = (Pago.objects
          .filter(prestamo__persona__user=request.user)
          .select_related('prestamo', 'prestamo__persona')
          .order_by('fecha_vencimiento', 'numero_cuota'))

    filas = [_fila(p, base) for p in qs]
    return render(request, 'pagos/lista_pagos.html', {'filas': filas, 'base': base})

@login_required
def pagos_pendientes(request):
    persona = getattr(request.user, 'persona', None)
    base = (persona.moneda_preferida if persona and persona.moneda_preferida else 'PEN').upper()

    qs = (Pago.objects
          .filter(prestamo__persona__user=request.user, estado='Pendiente')
          .select_related('prestamo', 'prestamo__persona')
          .order_by('fecha_vencimiento', 'numero_cuota'))

    filas = [_fila(p, base) for p in qs]
    return render(request, 'pagos/pendientes.html', {'filas': filas, 'base': base})

@login_required
def pagos_vencidos(request):
    persona = getattr(request.user, 'persona', None)
    base = (persona.moneda_preferida if persona and persona.moneda_preferida else 'PEN').upper()
    hoy = timezone.localdate()

    qs = (Pago.objects
          .filter(prestamo__persona__user=request.user, estado='Pendiente', fecha_vencimiento__lt=hoy)
          .select_related('prestamo', 'prestamo__persona')
          .order_by('fecha_vencimiento', 'numero_cuota'))

    filas = [_fila(p, base) for p in qs]
    return render(request, 'pagos/vencidos.html', {'filas': filas, 'base': base})

@login_required
@require_POST
def marcar_pagado(request, pago_id: int):
    pago = get_object_or_404(Pago, pk=pago_id, prestamo__persona__user=request.user)
    pago.fecha_pago = timezone.now()
    pago.estado = 'Pagado'

    try:
        base_mon = pago.prestamo.moneda_prestamo or 'PEN'
        dest_mon = (getattr(request.user.persona, 'moneda_preferida', None) or 'PEN').upper()
        tc = obtener_tipo_cambio(base_mon, dest_mon, pago.fecha_pago.date())
        if hasattr(pago, 'tc_fijo'):
            pago.tc_fijo = tc
        if hasattr(pago, 'monto_base_fijo'):
            pago.monto_base_fijo = pago.monto
        if hasattr(pago, 'monto_destino_fijo'):
            pago.monto_destino_fijo = round(pago.monto * (tc or 1), 2)
        if hasattr(pago, 'base_fija'):
            pago.base_fija = base_mon
        if hasattr(pago, 'destino_fijo'):
            pago.destino_fijo = dest_mon
    except Exception:
        messages.warning(request, 'Pago marcado, pero no se pudo registrar el tipo de cambio.')

    pago.save()
    messages.success(request, 'Pago marcado como Pagado.')
    return redirect('pagos:lista_pagos')
