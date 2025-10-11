from django.db import models
from Pagos.models import Pago

class Alerta(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Enviada', 'Enviada'),
        ('Cancelada', 'Cancelada'),
    ]

    id_alerta = models.AutoField(primary_key=True)
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='alertas')
    fecha_alerta = models.DateField()
    mensaje = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')

    def __str__(self):
        return f"Alerta para cuota {self.pago.numero_cuota} - {self.estado}"
