from django.db import models
from Persona.models import Persona

class Historial(models.Model):
    id_historial = models.AutoField(primary_key=True)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, related_name='historiales')
    accion = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.persona.nombres} - {self.accion[:50]}..."
