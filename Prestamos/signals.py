from decimal import Decimal, ROUND_HALF_UP, getcontext
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Prestamo
from .utils import add_months
from Pagos.models import Pago

getcontext().prec = 28  # precisión decente para cálculos

def _to_dec(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))

def _round2(x: Decimal) -> Decimal:
    return x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def _i_mensual_desde_tea(tea_percent: Decimal) -> Decimal:
    """
    Convierte TEA (porcentaje) a tasa mensual equivalente (efectiva):
    i = (1 + TEA)^(1/12) - 1
    """
    tea = _to_dec(tea_percent or 0) / Decimal('100')
    if tea <= 0:
        return Decimal('0')
    # usamos float para la potencia fraccionaria y regresamos a Decimal
    i_float = (1.0 + float(tea)) ** (1.0/12.0) - 1.0
    return Decimal(str(i_float))

def generar_cuotas(prestamo: Prestamo):
    """
    Genera cuotas para el préstamo con:
      - Sistema francés cuando tasa_interes > 0 (cuota fija).
      - Prorrateo simple cuando tasa_interes == 0.
    Guarda en Pago.monto la cuota del mes (capital+interés).

    Primera cuota: fecha_inicio + 1 mes (luego +2, +3, ...).
    """
    # evitar duplicados
    if Pago.objects.filter(prestamo=prestamo).exists():
        return

    n = int(prestamo.cuotas_totales or 0)
    if n <= 0:
        return

    P = _to_dec(prestamo.monto_total)
    i = _i_mensual_desde_tea(_to_dec(prestamo.tasa_interes or 0))

    montos = []

    if i <= 0:
        # Sin interés: prorrateo
        base = _round2(P / Decimal(n))
        acum = Decimal('0.00')
        for k in range(1, n+1):
            if k == n:
                monto = _round2(P - acum)
            else:
                monto = base
                acum += base
            montos.append(monto)
    else:
        # Francés: cuota fija
        uno_mas_i = Decimal('1') + i
        # cuota = P * i / (1 - (1+i)^-n)
        cuota = P * i / (Decimal('1') - (uno_mas_i ** Decimal(-n)))
        cuota = _round2(cuota)
        total_teorico = _round2(cuota * Decimal(n))

        saldo = P
        sum_asignado = Decimal('0.00')
        for k in range(1, n+1):
            interes = _round2(saldo * i)
            if k == n:
                # última: que cierre exacto al total_teorico
                monto = _round2(total_teorico - sum_asignado)
            else:
                monto = cuota
                sum_asignado += monto
            capital = _round2(monto - interes)
            saldo = _round2(saldo - capital)
            if saldo < 0:
                saldo = Decimal('0.00')
            montos.append(monto)

    # Crear pagos (1ª cuota = fecha_inicio + 1 mes)
    for idx, monto in enumerate(montos, start=1):
        fecha_venc = add_months(prestamo.fecha_inicio, idx)
        Pago.objects.create(
            prestamo=prestamo,
            numero_cuota=idx,
            monto=monto,
            fecha_vencimiento=fecha_venc,
            estado='Pendiente',
        )

@receiver(post_save, sender=Prestamo)
def crear_cuotas_automaticas(sender, instance: Prestamo, created, **kwargs):
    if created:
        generar_cuotas(instance)
