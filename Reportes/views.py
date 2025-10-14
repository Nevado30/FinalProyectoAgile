from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from Pagos.models import Pago
from Moneda.services import convertir_monto

def _month_bounds(d: date):
    first = d.replace(day=1)
    if first.month == 12:
        nxt = first.replace(year=first.year + 1, month=1, day=1)
    else:
        nxt = first.replace(month=first.month + 1, day=1)
    last = nxt - timedelta(days=1)
    return first, last

@login_required
def dashboard(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return render(request, 'reportes/dashboard.html', {'mensaje_persona': 'Completa tu perfil para ver reportes.'})

    base = (persona.moneda_preferida or 'PEN').upper()

    hoy = date.today()
    primer_dia, ultimo_dia = _month_bounds(hoy)

    qs = (Pago.objects
          .filter(prestamo__persona=persona, fecha_vencimiento__gte=primer_dia, fecha_vencimiento__lte=ultimo_dia)
          .select_related('prestamo', 'prestamo__persona')
          .order_by('fecha_vencimiento', 'numero_cuota'))

    def conv(p):
        origen = p.prestamo.moneda_prestamo or 'PEN'
        return convertir_monto(p.monto, origen, base, p.fecha_vencimiento)

    total_pendientes = sum((conv(p) for p in qs.filter(estado='Pendiente')), Decimal('0.00'))
    total_pagados_mes = sum((conv(p) for p in qs.filter(estado='Pagado')), Decimal('0.00'))
    total_vencidos = sum((conv(p) for p in qs.filter(estado='Pendiente', fecha_vencimiento__lt=hoy)), Decimal('0.00'))

    filas = [{'pago': p, 'monto_base': conv(p), 'monto_destino': None} for p in qs]

    ctx = {
        'primer_dia': primer_dia,
        'ultimo_dia': ultimo_dia,
        'total_pendientes': total_pendientes,
        'total_pagados_mes': total_pagados_mes,
        'total_vencidos': total_vencidos,
        'filas': filas,
        'base': base,
        'destino': base,  # ya no mostramos equivalente aquí
    }
    return render(request, 'reportes/dashboard.html', ctx)

@login_required
def agenda(request):
    """Próximos 7 días (incluye hoy) y vencidos de días anteriores."""
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return render(request, 'reportes/agenda.html', {'items': []})

    base = (persona.moneda_preferida or 'PEN').upper()
    hoy = date.today()
    fin = hoy + timedelta(days=7)

    vencidos = (Pago.objects
                .filter(prestamo__persona=persona, estado='Pendiente', fecha_vencimiento__lt=hoy)
                .select_related('prestamo', 'prestamo__persona'))
    proximos = (Pago.objects
                .filter(prestamo__persona=persona, estado='Pendiente', fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=fin)
                .select_related('prestamo', 'prestamo__persona')
                .order_by('fecha_vencimiento', 'numero_cuota'))

    items = []
    def _row(p):
        origen = p.prestamo.moneda_prestamo or 'PEN'
        monto = convertir_monto(p.monto, origen, base, p.fecha_vencimiento)
        estado = 'Vencido' if p.fecha_vencimiento < hoy else ('Hoy' if p.fecha_vencimiento == hoy else 'Próximo')
        return {'pago': p, 'monto': monto, 'estado': estado}

    items.extend(_row(p) for p in vencidos)
    items.extend(_row(p) for p in proximos)

    return render(request, 'reportes/agenda.html', {'items': items, 'base': base, 'hoy': hoy})
