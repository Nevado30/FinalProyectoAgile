from django.contrib import admin
from .models import Persona

@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'correo', 'telefono', 'fecha_registro')
    search_fields = ('nombres', 'apellidos', 'correo')
    list_filter = ('fecha_registro',)
    ordering = ('apellidos', 'nombres')
