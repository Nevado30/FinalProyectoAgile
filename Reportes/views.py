from datetime import date
import calendar

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from Persona.models import Persona
from Prestamos.models import Prestamo
from Pagos.models import Pago
from Moneda.services import obtener_tipo_cambio, convertir_monto


# pares simples para el selector
PARES_MONEDA = [
    ("USD", "PEN"),
    ("PEN", "USD"),
    ("USD", "EUR"),
    ("EUR", "USD"),
]


@login_required
def dashboard(request):
    hoy = date.today()
    primer_dia = date(hoy.year, hoy.month, 1)
    ultimo_dia = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])

    # filtros
    persona_id = request.GET.get('persona')
    prestamo_id = request.GET.get('prestamo')

    # monedas (con defaults)
    base = (request.GET.get('base') or "USD").upper()
    destino = (request.GET.get('destino') or "PEN").upper()

    # consultas
    pagos_qs = (
        Pago.objects
        .select_related('prestamo', 'prestamo__persona')
        .order_by('fecha_vencimiento', 'numero_cuota')
    )

    total_pendientes = Pago.objects.filter(estado='Pendiente').count()
    total_vencidos = Pago.objects.filter(
        estado__in=['Pendiente', 'Vencido'],
        fecha_vencimiento__lt=hoy
    ).count()
    total_pagados_mes = Pago.objects.filter(
        estado='Pagado',
        fecha_pago__gte=primer_dia,
        fecha_pago__lte=ultimo_dia
    ).count()

    pagos_mes = pagos_qs.filter(
        fecha_vencimiento__gte=primer_dia,
        fecha_vencimiento__lte=ultimo_dia
    )
    if persona_id:
        pagos_mes = pagos_mes.filter(prestamo__persona_id=persona_id)
    if prestamo_id:
        pagos_mes = pagos_mes.filter(prestamo_id=prestamo_id)

    # tasa (solo para mostrar)
    try:
        tc = obtener_tipo_cambio(base=base, destino=destino, para_fecha=hoy)
    except Exception:
        tc = None

    # convertir cada pago desde la moneda original del préstamo hacia base y destino
    pagos_mes_ctx = []
    for p in pagos_mes:
        origen = getattr(p.prestamo, 'moneda', 'PEN')  # si no tienes campo, asume PEN
        m_base = convertir_monto(p.monto, desde=origen, hacia=base,    para_fecha=hoy)
        m_dest = convertir_monto(p.monto, desde=origen, hacia=destino, para_fecha=hoy)
        pagos_mes_ctx.append((p, m_base, m_dest))

    personas = Persona.objects.all().order_by('apellidos', 'nombres')
    prestamos = Prestamo.objects.all().order_by('persona__apellidos', 'fecha_inicio')
    if persona_id:
        prestamos = prestamos.filter(persona_id=persona_id)

    contexto = {
        'hoy': hoy,
        'primer_dia': primer_dia,
        'ultimo_dia': ultimo_dia,
        'total_pendientes': total_pendientes,
        'total_vencidos': total_vencidos,
        'total_pagados_mes': total_pagados_mes,
        'pagos_mes_ctx': pagos_mes_ctx,
        'personas': personas,
        'prestamos': prestamos,
        'persona_id': int(persona_id) if persona_id else None,
        'prestamo_id': int(prestamo_id) if prestamo_id else None,
        'tc': tc,
        'base': base,
        'destino': destino,
        'PARES_MONEDA': PARES_MONEDA,
    }
    return render(request, 'reportes/dashboard.html', contexto)
