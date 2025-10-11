from django.contrib import admin
from .models import Prestamo

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('banco', 'persona', 'monto_total', 'fecha_inicio', 'cuotas_totales', 'tasa_interes')
    search_fields = ('banco', 'persona__nombres', 'persona__apellidos')
    list_filter = ('banco', 'fecha_inicio')
    ordering = ('persona', 'fecha_inicio')
