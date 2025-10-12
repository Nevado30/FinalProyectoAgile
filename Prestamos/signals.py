from decimal import Decimal, ROUND_HALF_UP
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Prestamo
from Pagos.models import Pago
from .utils import add_months

@receiver(post_save, sender=Prestamo)
def crear_cuotas_automaticas(sender, instance: Prestamo, created, **kwargs):
    """
    Al crear un préstamo, generar automáticamente N cuotas mensuales.
    Evita duplicados si ya existen pagos.
    """
    if not created:
        return

    if instance.pagos.exists():
        return

    # Monto de cada cuota (distribución simple)
    n = max(1, instance.cuotas_totales)
    monto_por_cuota = (Decimal(instance.monto_total) / Decimal(n)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    for i in range(1, n + 1):
        fecha_venc = add_months(instance.fecha_inicio, i - 1)
        Pago.objects.create(
            prestamo=instance,
            numero_cuota=i,
            monto=monto_por_cuota,
            fecha_vencimiento=fecha_venc,
            estado='Pendiente'
        )
