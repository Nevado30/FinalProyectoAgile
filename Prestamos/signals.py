from decimal import Decimal, ROUND_HALF_UP
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Prestamo
from .utils import add_months
from Pagos.models import Pago


@receiver(post_save, sender=Prestamo)
def crear_cuotas_automaticas(sender, instance: Prestamo, created, **kwargs):
    """
    Al crear un préstamo, genera N cuotas mensuales 'Pendiente'.
    Evita duplicar si ya existen pagos para ese préstamo.
    """
    if not created:
        return

    if Pago.objects.filter(prestamo=instance).exists():
        return

    n = int(instance.cuotas_totales or 0)
    if n <= 0:
        return

    total = Decimal(instance.monto_total)
    monto_base = (total / Decimal(n)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    acumulado = Decimal('0.00')
    for i in range(1, n + 1):
        if i == n:
            monto = (total - acumulado).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            monto = monto_base
            acumulado += monto

        fecha_venc = add_months(instance.fecha_inicio, i - 1)

        Pago.objects.create(
            prestamo=instance,
            numero_cuota=i,
            monto=monto,
            fecha_vencimiento=fecha_venc,
            estado='Pendiente',
        )
