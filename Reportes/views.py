from datetime import date, timedelta, datetime, time
import calendar
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone

from Pagos.models import Pago
from Moneda.services import convertir_monto


def _q2(x) -> Decimal:
    """Redondea a 2 decimales con HALF_UP (estilo financiero)."""
    try:
        d = Decimal(str(x))
    except Exception:
        d = Decimal(x)
    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _inicio_mes(d: date) -> date:
    return d.replace(day=1)


def _fin_mes(d: date) -> date:
    ultd = calendar.monthrange(d.year, d.month)[1]
    return date(d.year, d.month, ultd)


def _parse_mes_param(request) -> date:
    """
    Lee ?mes=YYYY-MM del querystring. Si no viene, usa el mes actual.
    """
    s = request.GET.get('mes')
    if s:
        try:
            y, m = s.split('-')
            return date(int(y), int(m), 1)
        except Exception:
            pass
    hoy = date.today()
    return date(hoy.year, hoy.month, 1)


def _mes_adj(d: date, delta_meses: int) -> date:
    """Mover 'd' delta_meses adelante/atrás manteniendo el día=1."""
    y = d.year + (d.month - 1 + delta_meses) // 12
    m = (d.month - 1 + delta_meses) % 12 + 1
    return date(y, m, 1)


@login_required
def dashboard(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return render(
            request,
            'reportes/dashboard.html',
            {'mensaje_persona': 'Completa tu perfil para ver reportes.'}
        )

    base = (persona.moneda_preferida or 'PEN').upper()

    # Mes seleccionado
    mes_base = _parse_mes_param(request)            # date(YYYY,MM,1)
    primer_dia = _inicio_mes(mes_base)
    ultimo_dia = _fin_mes(mes_base)

    # Variables que usa el template
    mes_str = mes_base.strftime('%Y-%m')
    prev_ym = _mes_adj(mes_base, -1).strftime('%Y-%m')
    next_ym = _mes_adj(mes_base, +1).strftime('%Y-%m')
    today = timezone.localdate()                    # fecha "hoy" según zona horaria Django
    today_ym = today.strftime('%Y-%m')

    # ================================
    # Pagos a mostrar en la tabla:
    # - Cuotas de ESTE mes
    # - Más cuotas de meses anteriores que sigan PENDIENTES
    # ================================
    qs_base = (
        Pago.objects
        .filter(prestamo__persona=persona)
        .filter(
            Q(fecha_vencimiento__gte=primer_dia, fecha_vencimiento__lte=ultimo_dia)
            | Q(fecha_vencimiento__lt=primer_dia, estado='Pendiente')
        )
        .select_related('prestamo', 'prestamo__persona')
        .order_by('fecha_vencimiento', 'numero_cuota')
    )

    # Solo pagos del mes actual (para los KPI que dicen "del mes")
    qs_mes = (
        Pago.objects
        .filter(
            prestamo__persona=persona,
            fecha_vencimiento__gte=primer_dia,
            fecha_vencimiento__lte=ultimo_dia,
        )
        .select_related('prestamo', 'prestamo__persona')
    )

    def conv(p):
        origen = p.prestamo.moneda_prestamo or 'PEN'
        return _q2(convertir_monto(p.monto, origen, base, p.fecha_vencimiento))

    # === Totales ===
    # Este mes debes pagar: todo lo pendiente que estás viendo (mes + atrasados)
    total_pendientes = sum(
        (conv(p) for p in qs_base.filter(estado='Pendiente')),
        Decimal('0.00')
    )

    # Pagado en el mes: solo cuotas de este mes con estado Pagado
    total_pagados_mes = sum(
        (conv(p) for p in qs_mes.filter(estado='Pagado')),
        Decimal('0.00')
    )

    # Pagos vencidos (globales): todo lo pendiente con fecha pasada, sin importar el mes
    qs_vencidos_global = (
        Pago.objects
        .filter(
            prestamo__persona=persona,
            estado='Pendiente',
            fecha_vencimiento__lt=today,
        )
        .select_related('prestamo', 'prestamo__persona')
    )

    total_vencidos = sum(
        (conv(p) for p in qs_vencidos_global),
        Decimal('0.00')
    )

    # ================================
    # Colores de filas (amarillo / rojo)
    # ================================

    # Convertir date → datetime local para evitar problemas de zona horaria
    def to_local_datetime(d: date) -> datetime:
        naive = datetime.combine(d, time.min)
        return timezone.make_aware(naive, timezone.get_current_timezone())

    today_dt = to_local_datetime(today)
    semana_fin_dt = today_dt + timedelta(days=7)

    def estado_visual(pago: Pago) -> str:
        pago_dt = to_local_datetime(pago.fecha_vencimiento)

        # Rojo: cualquier cuota NO pagada cuya fecha de vencimiento ya pasó
        if pago_dt < today_dt and pago.estado != 'Pagado':
            return 'vencido'

        # Amarillo: cuotas PENDIENTES que vencen entre hoy y los próximos 7 días
        if pago.estado == 'Pendiente' and today_dt <= pago_dt <= semana_fin_dt:
            return 'semana'

        return ''

    filas = [
        {
            'pago': p,
            'monto_base': conv(p),
            'monto_destino': None,
            'estado_visual': estado_visual(p),
        }
        for p in qs_base
    ]

    ctx = {
        'primer_dia': primer_dia,
        'ultimo_dia': ultimo_dia,
        'total_pendientes': total_pendientes,
        'total_pagados_mes': total_pagados_mes,
        'total_vencidos': total_vencidos,
        'filas': filas,
        'base': base,
        'destino': base,   # compatibilidad

        # Controles de navegación que espera el template
        'mes_str': mes_str,
        'prev_ym': prev_ym,
        'next_ym': next_ym,
        'today_ym': today_ym,
        'today': today,
    }
    return render(request, 'reportes/dashboard.html', ctx)


@login_required
def agenda(request):
    """Próximos 7 días (incluye hoy) y vencidos previos."""
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return render(request, 'reportes/agenda.html', {
            'items': [],
            'base': 'PEN',
            'hoy': date.today(),
        })

    base = (persona.moneda_preferida or 'PEN').upper()
    hoy = date.today()
    fin = hoy + timedelta(days=7)

    vencidos = (
        Pago.objects
        .filter(prestamo__persona=persona, estado='Pendiente', fecha_vencimiento__lt=hoy)
        .select_related('prestamo', 'prestamo__persona')
    )
    proximos = (
        Pago.objects
        .filter(prestamo__persona=persona, estado='Pendiente',
                fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=fin)
        .select_related('prestamo', 'prestamo__persona')
        .order_by('fecha_vencimiento', 'numero_cuota')
    )

    def row(p):
        origen = p.prestamo.moneda_prestamo or 'PEN'
        monto = convertir_monto(p.monto, origen, base, p.fecha_vencimiento)
        if p.fecha_vencimiento < hoy:
            estado = 'Vencido'
        elif p.fecha_vencimiento == hoy:
            estado = 'Hoy'
        else:
            estado = 'Próximo'
        return {'pago': p, 'monto': monto, 'estado': estado}

    items = [row(p) for p in vencidos] + [row(p) for p in proximos]

    return render(request, 'reportes/agenda.html', {
        'items': items,
        'base': base,
        'hoy': hoy,
    })
