from datetime import date
from django.core.management.base import BaseCommand
from Moneda.services import obtener_tipo_cambio

class Command(BaseCommand):
    help = "Actualiza/precarga el tipo de cambio USD→PEN del día actual."

    def handle(self, *args, **options):
        valor = obtener_tipo_cambio(base="USD", destino="PEN", para_fecha=date.today())
        self.stdout.write(self.style.SUCCESS(f"Tipo de cambio USD→PEN guardado: {valor}"))
