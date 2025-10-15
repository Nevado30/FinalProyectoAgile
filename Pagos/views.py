# Pagos/views.py
from decimal import Decimal, ROUND_HALF_UP
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from .models import Pago
from Moneda.services import convertir_monto, obtener_tipo_cambio

def _q2(x) -> Decimal:
    """Redondeo a 2 decimales (Decimal)."""
    try:
        d = Decimal(str(x))
    except Exception:
        d = Decimal(x)
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def _sym(mon: str) -> str:
    """Símbolo a mostrar delante del monto."""
    m = (mon or 'PEN').upper()
    return {'PEN': 'S/', 'USD': '$/', 'EUR': '€/'}.get(m, m + '/')

@login_required
def lista_pagos(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return render(request, 'pagos/lista_pagos.html', {'filas': [], 'page_obj': None})

    # Query base
    pagos_qs = (Pago.objects
                .filter(prestamo__persona=persona)
                .select_related('prestamo', 'prestamo__persona')
                .order_by('fecha_vencimiento', 'numero_cuota'))

    # Paginación (12 por página)
    paginator = Paginator(pagos_qs, 12)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    filas = []
    preferida = (persona.moneda_preferida or 'PEN').upper()

    for p in page_obj.object_list:
        origen = (p.prestamo.moneda_prestamo or 'PEN').upper()
        # Si tu modelo tiene `moneda_pago` úsalo; si no, caes a preferida del usuario
        destino = (getattr(p.prestamo, 'moneda_pago', None) or preferida).upper()

        # Base: el monto del pago (moneda del préstamo)
        monto_base = _q2(p.monto)

        # Equivalente: solo si cambia de moneda
        equiv = None
        if origen != destino:
            try:
                equiv = _q2(convertir_monto(p.monto, origen, destino, p.fecha_vencimiento))
            except Exception:
                equiv = None  # si la API falla, no rompe

        filas.append({
            'pago': p,
            'monto_base': monto_base,
            'equiv': equiv,                # Decimal o None
            'sym_origen': _sym(origen),    # 'S/' '$/' '€/'
            'sym_destino': _sym(destino),
        })

    ctx = {
        'filas': filas,
        'page_obj': page_obj,   # para los controles de paginación
    }
    return render(request, 'pagos/lista_pagos.html', ctx)
@login_required
def pagos_pendientes(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return render(request, 'pagos/pendientes.html', {'filas': []})

    preferida = (persona.moneda_preferida or 'PEN').upper()

    qs = (Pago.objects
          .filter(prestamo__persona=persona, estado='Pendiente')
          .select_related('prestamo', 'prestamo__persona')
          .order_by('fecha_vencimiento', 'numero_cuota'))

    filas = []
    for p in qs:
        origen = (p.prestamo.moneda_prestamo or 'PEN').upper()
        destino = (getattr(p.prestamo, 'moneda_pago', None) or preferida).upper()

        monto_base = _q2(p.monto)

        equiv = None
        if origen != destino:
            try:
                equiv = _q2(convertir_monto(p.monto, origen, destino, p.fecha_vencimiento))
            except Exception:
                equiv = None

        filas.append({
            'pago': p,
            'monto_base': monto_base,
            'equiv': equiv,
            'sym_origen': _sym(origen),
            'sym_destino': _sym(destino),
        })

    return render(request, 'pagos/pendientes.html', {'filas': filas})


@login_required
def pagos_vencidos(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return render(request, 'pagos/vencidos.html', {'filas': []})

    preferida = (persona.moneda_preferida or 'PEN').upper()
    hoy = timezone.localdate()

    qs = (Pago.objects
          .filter(prestamo__persona=persona, estado='Pendiente', fecha_vencimiento__lt=hoy)
          .select_related('prestamo', 'prestamo__persona')
          .order_by('fecha_vencimiento', 'numero_cuota'))

    filas = []
    for p in qs:
        origen = (p.prestamo.moneda_prestamo or 'PEN').upper()
        destino = (getattr(p.prestamo, 'moneda_pago', None) or preferida).upper()

        monto_base = _q2(p.monto)

        equiv = None
        if origen != destino:
            try:
                equiv = _q2(convertir_monto(p.monto, origen, destino, p.fecha_vencimiento))
            except Exception:
                equiv = None

        filas.append({
            'pago': p,
            'monto_base': monto_base,
            'equiv': equiv,
            'sym_origen': _sym(origen),
            'sym_destino': _sym(destino),
        })

    return render(request, 'pagos/vencidos.html', {'filas': filas})

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
