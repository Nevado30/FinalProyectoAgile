from django.contrib import admin
from .models import Historial

@admin.register(Historial)
class HistorialAdmin(admin.ModelAdmin):
    list_display = ('persona', 'accion', 'fecha_registro')
    search_fields = ('persona__nombres', 'accion')
    list_filter = ('fecha_registro',)
    ordering = ('-fecha_registro',)
