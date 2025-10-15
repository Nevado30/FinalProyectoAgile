from django.db import models
from Persona.models import Persona
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
 
MONEDAS = (
    ('PEN', 'PEN'),
    ('USD', 'USD'),
    ('EUR', 'EUR'),
)

class Prestamo(models.Model):
    id_prestamo   = models.AutoField(primary_key=True)
    persona       = models.ForeignKey(Persona, on_delete=models.CASCADE)
    banco         = models.CharField(max_length=100)
    descripcion   = models.TextField(blank=True, null=True)
    monto_total   = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')),
                    MaxValueValidator(Decimal('400000'))]
    )

    fecha_inicio  = models.DateField()

    cuotas_totales = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(36)]
    )

    tasa_interes   = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0')),
                    MaxValueValidator(Decimal('116'))]
    )

    # Monedas
    moneda_prestamo = models.CharField(max_length=3, choices=MONEDAS, default='PEN')
    moneda_pago     = models.CharField(max_length=3, choices=MONEDAS, default='PEN')

    def __str__(self):
        return f"{self.banco} — {self.persona} — #{self.id_prestamo}"
