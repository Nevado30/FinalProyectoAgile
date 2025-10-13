from datetime import date
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import Pago
from Moneda.services import obtener_tipo_cambio, convertir_monto


@login_required
def pagos_pendientes(request):
    base = (request.GET.get('base') or 'PEN').upper()
    destino = (request.GET.get('destino') or 'USD').upper()

    pagos = (Pago.objects
             .select_related('prestamo', 'prestamo__persona')
             .filter(estado='Pendiente')
             .order_by('fecha_vencimiento', 'prestamo__persona__apellidos', 'numero_cuota'))
    return render(request, 'pagos/pendientes.html', {'pagos': pagos, 'base': base, 'destino': destino})


@login_required
def pagos_vencidos(request):
    base = (request.GET.get('base') or 'PEN').upper()
    destino = (request.GET.get('destino') or 'USD').upper()

    hoy = date.today()
    pagos = (Pago.objects
             .select_related('prestamo', 'prestamo__persona')
             .filter(estado__in=['Pendiente', 'Vencido'], fecha_vencimiento__lt=hoy)
             .order_by('fecha_vencimiento'))
    return render(request, 'pagos/vencidos.html', {'pagos': pagos, 'hoy': hoy, 'base': base, 'destino': destino})


@login_required
@require_POST
def marcar_pagado(request, pago_id):
    pago = get_object_or_404(Pago, pk=pago_id)
    hoy = date.today()

    base = (request.POST.get('base') or 'PEN').upper()
    destino = (request.POST.get('destino') or 'USD').upper()
    origen = getattr(pago.prestamo, 'moneda', 'PEN')

    tc = Decimal(obtener_tipo_cambio(base=origen, destino=destino, para_fecha=hoy))
    m_base = convertir_monto(pago.monto, desde=origen, hacia=base,    para_fecha=hoy)
    m_dest = convertir_monto(pago.monto, desde=origen, hacia=destino, para_fecha=hoy)

    pago.estado = 'Pagado'
    pago.fecha_pago = hoy
    pago.base_fija = base
    pago.destino_fijo = destino
    pago.tc_fijo = tc
    pago.monto_base_fijo = m_base
    pago.monto_destino_fijo = m_dest
    pago.save()

    next_url = request.POST.get('next') or reverse('pagos:pendientes')
    return redirect(next_url)


@login_required
def lista_pagos(request):
    base = (request.GET.get('base') or 'PEN').upper()
    destino = (request.GET.get('destino') or 'USD').upper()

    pagos = (Pago.objects
             .select_related('prestamo', 'prestamo__persona')
             .order_by('fecha_vencimiento', 'numero_cuota'))

    hoy = date.today()
    pagos_ctx = []
    for p in pagos:
        origen = getattr(p.prestamo, 'moneda', 'PEN')
        if p.estado == 'Pagado' and p.monto_base_fijo is not None:
            m_base = p.monto_base_fijo
            m_dest = p.monto_destino_fijo
        else:
            m_base = convertir_monto(p.monto, desde=origen, hacia=base,    para_fecha=hoy)
            m_dest = convertir_monto(p.monto, desde=origen, hacia=destino, para_fecha=hoy)
        pagos_ctx.append((p, m_base, m_dest))

    return render(
        request,
        'pagos/lista_pagos.html',
        {'pagos_ctx': pagos_ctx, 'base': base, 'destino': destino}
    )
