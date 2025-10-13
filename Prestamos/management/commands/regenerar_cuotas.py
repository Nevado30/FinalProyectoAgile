from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand

from Prestamos.models import Prestamo
from Prestamos.utils import add_months
from Pagos.models import Pago


class Command(BaseCommand):
    help = "Genera cuotas para préstamos que aún no tienen pagos creados."

    def handle(self, *args, **options):
        creadas = 0
        for pr in Prestamo.objects.all():
            if Pago.objects.filter(prestamo=pr).exists():
                continue

            n = int(pr.cuotas_totales or 0)
            if n <= 0:
                continue

            total = Decimal(pr.monto_total)
            monto_base = (total / Decimal(n)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            acumulado = Decimal('0.00')

            for i in range(1, n + 1):
                if i == n:
                    monto = (total - acumulado).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                else:
                    monto = monto_base
                    acumulado += monto

                Pago.objects.create(
                    prestamo=pr,
                    numero_cuota=i,
                    monto=monto,
                    fecha_vencimiento=add_months(pr.fecha_inicio, i - 1),
                    estado='Pendiente',
                )
                creadas += 1

        self.stdout.write(self.style.SUCCESS(f'Cuotas creadas: {creadas}'))
