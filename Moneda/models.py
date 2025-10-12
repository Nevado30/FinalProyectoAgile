from django.db import models

class TipoCambio(models.Model):
    """
    Cache local del tipo de cambio por fecha y par de monedas.
    Ej.: base='USD', destino='PEN', fecha='2025-10-12', valor=3.80
    """
    fecha = models.DateField()
    base = models.CharField(max_length=3)      # p.ej. 'USD'
    destino = models.CharField(max_length=3)   # p.ej. 'PEN'
    valor = models.DecimalField(max_digits=12, decimal_places=6)
    obtenido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('fecha', 'base', 'destino')

    def __str__(self):
        return f"{self.fecha} {self.base}->{self.destino} = {self.valor}"
