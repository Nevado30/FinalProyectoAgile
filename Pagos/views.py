from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from .models import Pago
from Moneda.services import obtener_tipo_cambio, convertir_monto


def _filas_convertidas(qs, base, destino):
    filas = []
    for p in qs.order_by('fecha_vencimiento', 'numero_cuota'):
        try:
            monto_base = convertir_monto(p.monto, base, base, p.fecha_vencimiento)
            monto_destino = convertir_monto(p.monto, base, destino, p.fecha_vencimiento)
        except Exception:
            monto_base = p.monto
            monto_destino = p.monto
        filas.append({'pago': p, 'monto_base': monto_base, 'monto_destino': monto_destino})
    return filas


@login_required
def lista_pagos(request):
    base = (request.GET.get('base') or 'PEN').upper()
    destino = (request.GET.get('destino') or 'PEN').upper()

    qs = (Pago.objects
          .filter(prestamo__persona__user=request.user)
          .select_related('prestamo', 'prestamo__persona'))

    ctx = {
        'base': base,
        'destino': destino,
        'filas': _filas_convertidas(qs, base, destino),
    }
    return render(request, 'pagos/lista_pagos.html', ctx)


@login_required
def pagos_pendientes(request):
    base = (request.GET.get('base') or 'PEN').upper()
    destino = (request.GET.get('destino') or 'PEN').upper()

    qs = (Pago.objects
          .filter(prestamo__persona__user=request.user, estado='Pendiente')
          .select_related('prestamo', 'prestamo__persona'))

    ctx = {
        'base': base,
        'destino': destino,
        'filas': _filas_convertidas(qs, base, destino),
    }
    return render(request, 'pagos/pendientes.html', ctx)


@login_required
def pagos_vencidos(request):
    base = (request.GET.get('base') or 'PEN').upper()
    destino = (request.GET.get('destino') or 'PEN').upper()
    hoy = timezone.localdate()

    qs = (Pago.objects
          .filter(prestamo__persona__user=request.user, estado='Pendiente', fecha_vencimiento__lt=hoy)
          .select_related('prestamo', 'prestamo__persona'))

    ctx = {
        'base': base,
        'destino': destino,
        'filas': _filas_convertidas(qs, base, destino),
    }
    return render(request, 'pagos/vencidos.html', ctx)


@login_required
@require_POST
def marcar_pagado(request, pago_id: int):
    pago = get_object_or_404(Pago, pk=pago_id, prestamo__persona__user=request.user)
    pago.fecha_pago = timezone.now()
    pago.estado = 'Pagado'

    try:
        base_mon = getattr(pago, 'base_fija', None) or 'PEN'
        dest_mon = getattr(pago, 'destino_fijo', None) or 'PEN'
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
