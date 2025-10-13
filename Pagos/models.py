from django.db import models
from Prestamos.models import Prestamo

class Pago(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Vencido', 'Vencido'),
    ]

    id_pago = models.AutoField(primary_key=True)
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='pagos')
    numero_cuota = models.PositiveIntegerField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')

    # --- Snapshot al pagar (para que no cambie con el selector de moneda) ---
    base_fija = models.CharField(max_length=3, blank=True, null=True)
    destino_fijo = models.CharField(max_length=3, blank=True, null=True)
    tc_fijo = models.DecimalField(max_digits=12, decimal_places=6, blank=True, null=True)
    monto_base_fijo = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    monto_destino_fijo = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    # ------------------------------------------------------------------------

    def __str__(self):
        return f"Cuota {self.numero_cuota} - {self.prestamo.banco} ({self.estado})"
