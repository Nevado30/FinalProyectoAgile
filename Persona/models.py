from django.db import models
from django.contrib.auth.models import User

class Persona(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='persona')
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f'{self.apellidos}, {self.nombres}'
