# Pagos/views.py
from decimal import Decimal, ROUND_HALF_UP

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.urls import reverse

import mercadopago

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


# ======================================================
# LISTADO / PENDIENTES / VENCIDOS
# ======================================================

@login_required
def lista_pagos(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return render(request, 'pagos/lista_pagos.html', {'filas': [], 'page_obj': None})

    pagos_qs = (
        Pago.objects
        .filter(prestamo__persona=persona)
        .select_related('prestamo', 'prestamo__persona')
        .order_by('fecha_vencimiento', 'numero_cuota')
    )

    paginator = Paginator(pagos_qs, 12)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    filas = []
    preferida = (persona.moneda_preferida or 'PEN').upper()

    for p in page_obj.object_list:
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

    ctx = {
        'filas': filas,
        'page_obj': page_obj,
    }
    return render(request, 'pagos/lista_pagos.html', ctx)


@login_required
def pagos_pendientes(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        return render(request, 'pagos/pendientes.html', {'filas': []})

    preferida = (persona.moneda_preferida or 'PEN').upper()

    qs = (
        Pago.objects
        .filter(prestamo__persona=persona, estado='Pendiente')
        .select_related('prestamo', 'prestamo__persona')
        .order_by('fecha_vencimiento', 'numero_cuota')
    )

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

    qs = (
        Pago.objects
        .filter(prestamo__persona=persona, estado='Pendiente', fecha_vencimiento__lt=hoy)
        .select_related('prestamo', 'prestamo__persona')
        .order_by('fecha_vencimiento', 'numero_cuota')
    )

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


# ======================================================
# MARCAR PAGADO (MANUAL / BACKUP)
# ======================================================

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


# ======================================================
# MERCADO PAGO
# ======================================================

def _monto_en_pen_desde_pago(pago: Pago) -> float:
    """
    Convierte el monto del pago a PEN para Mercado Pago.
    Si ya está en PEN, solo lo devuelve.
    """
    origen = (pago.prestamo.moneda_prestamo or "PEN").upper()
    destino = "PEN"

    if origen == destino:
        return float(pago.monto)

    monto_pen = convertir_monto(
        pago.monto,
        origen,
        destino,
        pago.fecha_vencimiento
    )
    return float(monto_pen)


@login_required
def pagar_cuota(request, pago_id: int):
    """
    Crea una preferencia de pago en Mercado Pago para la cuota indicada
    y redirige al Checkout Pro.
    """
    pago = get_object_or_404(
        Pago,
        pk=pago_id,
        prestamo__persona__user=request.user,
        estado="Pendiente",
    )

    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    monto_pen = _monto_en_pen_desde_pago(pago)

    back_success = request.build_absolute_uri(reverse("pagos:mp_success"))
    back_failure = request.build_absolute_uri(reverse("pagos:mp_failure"))
    back_pending = request.build_absolute_uri(reverse("pagos:mp_pending"))

    preference_data = {
        "items": [
            {
                "id": str(pago.pk),
                "title": f"Cuota {pago.numero_cuota} - {pago.prestamo.banco}",
                "quantity": 1,
                "currency_id": "PEN",
                "unit_price": monto_pen,
            }
        ],
        "payer": {
            "email": request.user.email or pago.prestamo.persona.correo,
        },
        "back_urls": {
            "success": back_success,
            "failure": back_failure,
            "pending": back_pending,
        },
      #  "auto_return": "approved", luego lo implemento
        "metadata": {
            "pago_id": pago.pk,
        },
    }

    try:
        result = sdk.preference().create(preference_data)
        print("=== MERCADO PAGO RESULT ===")
        print(result)
    except Exception as e:
        print("=== MERCADO PAGO EXCEPTION ===")
        print(e)
        messages.error(request, f"Error al contactar a Mercado Pago: {e}")
        return redirect("pagos:lista_pagos")

    status = result.get("status")
    response = result.get("response")

    if status != 201:
        # Leer mensaje y causas que devuelve Mercado Pago
        error_msg = ""
        causes_txt = ""

        if isinstance(response, dict):
            error_msg = response.get("message", "")
            causes = response.get("cause") or []
            if isinstance(causes, list) and causes:
                # Ej: [{"code": "123", "description": "algo"}]
                causas_str = []
                for c in causes:
                    if isinstance(c, dict):
                        desc = c.get("description") or c.get("code") or str(c)
                        causas_str.append(desc)
                    else:
                        causas_str.append(str(c))
                causes_txt = " | ".join(causas_str)
        else:
            error_msg = str(response)

        print("=== MP STATUS ERROR ===", status, error_msg, causes_txt)

        messages.error(
            request,
            f"No se pudo iniciar el pago en Mercado Pago (status {status}). "
            f"{error_msg} {causes_txt}"
        )
        return redirect("pagos:lista_pagos")


    pref = response
    init_point = pref.get("init_point")

    pago.mp_preference_id = pref.get("id")
    pago.save(update_fields=["mp_preference_id"])

    return redirect(init_point)


@login_required
@require_GET
def mp_success(request):
    """
    Mercado Pago redirige aquí cuando el pago termina con estado 'approved'
    (o similar). Se marca la cuota como Pagada.
    """
    pref_id = request.GET.get("preference_id")
    payment_id = request.GET.get("payment_id") or request.GET.get("collection_id")
    status = request.GET.get("collection_status") or request.GET.get("status")

    if not pref_id:
        messages.error(request, "Falta el identificador de la preferencia.")
        return redirect("pagos:lista_pagos")

    pago = get_object_or_404(
        Pago,
        mp_preference_id=pref_id,
        prestamo__persona__user=request.user,
    )

    pago.mp_payment_id = payment_id or ""

    if status == "approved":
        if pago.estado != "Pagado":
            pago.fecha_pago = timezone.now()
            pago.estado = "Pagado"

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
                messages.warning(
                    request,
                    "Pago aprobado, pero no se pudo registrar el tipo de cambio."
                )

        pago.save()
        messages.success(request, "Pago registrado correctamente.")
    else:
        # approved, in_process, pending, etc.
        pago.save(update_fields=["mp_payment_id"])
        messages.info(request, f"El pago quedó con estado: {status or 'desconocido'}.")

    return redirect("pagos:lista_pagos")


@login_required
@require_GET
def mp_failure(request):
    messages.error(request, "El pago fue rechazado o cancelado.")
    return redirect("pagos:pendientes")


@login_required
@require_GET
def mp_pending(request):
    messages.info(request, "El pago quedó pendiente de aprobación.")
    return redirect("pagos:pendientes")
