from django.contrib import admin
from .models import Pago

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('prestamo', 'numero_cuota', 'monto', 'fecha_vencimiento', 'estado')
    list_filter = ('estado', 'fecha_vencimiento')
    search_fields = ('prestamo__banco', 'prestamo__persona__nombres')
    ordering = ('fecha_vencimiento',)
