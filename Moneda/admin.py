from django.contrib import admin
from .models import TipoCambio

@admin.register(TipoCambio)
class TipoCambioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'base', 'destino', 'valor', 'obtenido_en')
    list_filter = ('base', 'destino', 'fecha')
    search_fields = ('base', 'destino')
    ordering = ('-fecha', 'base', 'destino')
