from datetime import date
import calendar
from django.shortcuts import render
from Persona.models import Persona
from Prestamos.models import Prestamo
from Pagos.models import Pago

def dashboard(request):
    # Rango del mes actual (por fecha de vencimiento)
    hoy = date.today()
    primer_dia = date(hoy.year, hoy.month, 1)
    ultimo_dia = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])

    # Filtros GET
    persona_id = request.GET.get('persona')
    prestamo_id = request.GET.get('prestamo')

    pagos_qs = (Pago.objects
                    .select_related('prestamo', 'prestamo__persona')
                    .order_by('fecha_vencimiento', 'numero_cuota'))

    # Conteos generales
    total_pendientes = Pago.objects.filter(estado='Pendiente').count()
    total_vencidos = Pago.objects.filter(
        estado__in=['Pendiente', 'Vencido'],
        fecha_vencimiento__lt=hoy
    ).count()
    total_pagados_mes = Pago.objects.filter(
        estado='Pagado', fecha_pago__gte=primer_dia, fecha_pago__lte=ultimo_dia
    ).count()

    # Listado del mes actual (por vencimiento)
    pagos_mes = pagos_qs.filter(fecha_vencimiento__gte=primer_dia,
                                fecha_vencimiento__lte=ultimo_dia)

    # Aplicar filtros
    if persona_id:
        pagos_mes = pagos_mes.filter(prestamo__persona_id=persona_id)
    if prestamo_id:
        pagos_mes = pagos_mes.filter(prestamo_id=prestamo_id)

    # Población de selects
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

        'pagos_mes': pagos_mes,
        'personas': personas,
        'prestamos': prestamos,
        'persona_id': int(persona_id) if persona_id else None,
        'prestamo_id': int(prestamo_id) if prestamo_id else None,
    }
    return render(request, 'reportes/dashboard.html', contexto)
