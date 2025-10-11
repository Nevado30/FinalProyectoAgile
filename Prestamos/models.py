from django.db import models
from Persona.models import Persona

class Prestamo(models.Model):
    id_prestamo = models.AutoField(primary_key=True)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='prestamos')
    banco = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_inicio = models.DateField()
    cuotas_totales = models.PositiveIntegerField()
    tasa_interes = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # opcional

    def __str__(self):
        return f"{self.banco} - {self.persona.nombres} {self.persona.apellidos}"
