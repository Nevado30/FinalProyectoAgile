from django.db import models
from django.contrib.auth.models import User

class Persona(models.Model):
    id_persona = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
