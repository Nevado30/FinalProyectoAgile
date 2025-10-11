from django.contrib import admin
from .models import Alerta

@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('pago', 'fecha_alerta', 'estado')
    list_filter = ('estado', 'fecha_alerta')
    search_fields = ('pago__prestamo__banco',)
    ordering = ('fecha_alerta',)
