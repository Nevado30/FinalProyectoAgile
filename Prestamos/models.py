from django.db import models
from Persona.models import Persona

MONEDAS = (
    ('PEN', 'PEN'),
    ('USD', 'USD'),
    ('EUR', 'EUR'),
)

class Prestamo(models.Model):
    id_prestamo = models.AutoField(primary_key=True)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    banco = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_inicio = models.DateField()
    cuotas_totales = models.IntegerField()
    tasa_interes = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # % anual (TEA)

    # ▼ NUEVO: monedas
    moneda_prestamo = models.CharField(max_length=3, choices=MONEDAS, default='PEN')  # en qué está el préstamo
    moneda_pago = models.CharField(max_length=3, choices=MONEDAS, default='PEN')      # en qué sueles pagarlo/verlo

    def __str__(self):
        return f"{self.banco} — {self.persona} — #{self.id_prestamo}"
