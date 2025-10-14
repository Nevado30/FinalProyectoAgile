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
    if not persona:
        return render(request, 'pagos/lista.html', {'filas': []})

    pagos = (Pago.objects
             .filter(prestamo__persona=persona)
             .select_related('prestamo', 'prestamo__persona')
             .order_by('fecha_vencimiento', 'numero_cuota'))

    filas = []
    destino_global = (persona.moneda_preferida or 'PEN').upper()

    # Si TODOS los préstamos usan la misma moneda de pago => úsala para header.
    # Si cada préstamo define la suya, pondremos el header dinámico con un fallback al global.
    destino_header = destino_global

    show_equiv = False
    for p in pagos:
        origen = (p.prestamo.moneda_prestamo or 'PEN').upper()
        destino = (getattr(p.prestamo, 'moneda_pago', None) or destino_global).upper()

        if origen != destino:
            show_equiv = True

        try:
            equiv = convertir_monto(p.monto, origen, destino, p.fecha_vencimiento) if origen != destino else None
        except Exception:
            equiv = None  # si falla la API, no rompas la vista

        filas.append({
            'pago': p,
            'monto_base': p.monto,   # ya está en la moneda del préstamo
            'equiv': equiv,          # Decimal o None
            'origen': origen,
            'destino': destino,
        })

        # Para el header, si alguna fila usa otra moneda destino, mantenemos el global
        # (si prefieres, podrías detectar la más común).
        destino_header = destino

    ctx = {
        'filas': filas,
        'show_equiv': show_equiv,
        'destino': destino_header,   # para el título "Equivalente ({{ destino }})"
    }
    return render(request, 'pagos/lista_pagos.html', ctx)

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
