from datetime import date
import calendar

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from Pagos.models import Pago
from Prestamos.models import Prestamo
from Moneda.services import convertir_monto, obtener_tipo_cambio

# Pares disponibles
PARES_MONEDA = [
    ("PEN", "PEN"),
    ("PEN", "USD"),
    ("PEN", "EUR"),
    ("USD", "USD"),
    ("USD", "PEN"),
    ("USD", "EUR"),
    ("EUR", "EUR"),
    ("EUR", "PEN"),
    ("EUR", "USD"),
]

@login_required
def dashboard(request):
    """
    Dashboard mensual por USUARIO (multi-tenant).
      - Cantidad de pendientes (global del usuario)
      - Cantidad de vencidos (pendiente con fecha < hoy)
      - Cantidad de pagados en el mes
      - Tabla de pagos del mes con conversión base→destino
    """
    hoy = date.today()
    primer_dia = date(hoy.year, hoy.month, 1)
    ultimo_dia = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])

    base = (request.GET.get('base') or "PEN").upper()
    destino = (request.GET.get('destino') or "PEN").upper()
    prestamo_id = (request.GET.get('prestamo') or "").strip()

    persona = getattr(request.user, 'persona', None)

    # Si el usuario no tiene Persona vinculada, mostramos aviso
    if persona is None:
        ctx = {
            'mensaje_persona': 'Tu usuario no está vinculado a una Persona. Completa tu perfil para ver datos.',
            'PARES_MONEDA': PARES_MONEDA,
            'base': base,
            'destino': destino,
            'primer_dia': primer_dia,
            'ultimo_dia': ultimo_dia,
            'prestamos': [],
            'prestamo_id': "",
            'tc_hoy': None,
            'pendientes_count': 0,
            'vencidos_count': 0,
            'pagados_mes_count': 0,
            'filas': [],
            'today': hoy,
        }
        return render(request, 'reportes/dashboard.html', ctx)

    # Prestamos del usuario (OJO: PK = id_prestamo, no 'id')
    prestamos_user = Prestamo.objects.filter(persona=persona).order_by('id_prestamo')

    # Pagos SOLO del usuario
    pagos_qs = (
        Pago.objects
        .filter(prestamo__persona=persona)
        .select_related('prestamo', 'prestamo__persona')
    )

    # Mes actual
    pagos_mes = pagos_qs.filter(fecha_vencimiento__range=(primer_dia, ultimo_dia))

    # Filtro por préstamo validando que sea del usuario
    if prestamo_id and prestamo_id.isdigit():
        pagos_qs = pagos_qs.filter(prestamo__id_prestamo=int(prestamo_id))
        pagos_mes = pagos_mes.filter(prestamo__id_prestamo=int(prestamo_id))

    # === CONTADORES (CANTIDAD) ===
    pendientes_count = pagos_qs.filter(estado='Pendiente').count()
    vencidos_count = pagos_qs.filter(estado='Pendiente', fecha_vencimiento__lt=hoy).count()
    pagados_mes_count = pagos_mes.filter(estado='Pagado').count()

    # === Tabla del MES con conversión ===
    filas = []
    for p in pagos_mes.order_by('fecha_vencimiento', 'numero_cuota'):
        try:
            monto_base = convertir_monto(p.monto, base, base, p.fecha_vencimiento)
            monto_destino = convertir_monto(p.monto, base, destino, p.fecha_vencimiento)
        except Exception:
            monto_base = p.monto
            monto_destino = p.monto

        filas.append({
            'pago': p,
            'monto_base': monto_base,
            'monto_destino': monto_destino,
        })

    # Tipo de cambio del día
    try:
        tc_hoy = obtener_tipo_cambio(base, destino, hoy)
    except Exception:
        tc_hoy = None

    ctx = {
        'primer_dia': primer_dia,
        'ultimo_dia': ultimo_dia,
        'PARES_MONEDA': PARES_MONEDA,
        'base': base,
        'destino': destino,

        'prestamos': prestamos_user,
        'prestamo_id': prestamo_id,  # string, se compara en el template

        'tc_hoy': tc_hoy,

        'pendientes_count': pendientes_count,
        'vencidos_count': vencidos_count,
        'pagados_mes_count': pagados_mes_count,

        'filas': filas,
        'today': hoy,
    }
    return render(request, 'reportes/dashboard.html', ctx)
