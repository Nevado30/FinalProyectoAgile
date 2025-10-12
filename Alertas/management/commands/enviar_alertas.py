from django.core.management.base import BaseCommand
from Alertas.services import generar_y_enviar_alertas

class Command(BaseCommand):
    help = "Genera y envía alertas de pagos próximos (N días) y vencidos."

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=3, help='Días antes del vencimiento')

    def handle(self, *args, **options):
        dias = options['dias']
        resumen = generar_y_enviar_alertas(dias_antes=dias)
        self.stdout.write(self.style.SUCCESS(
            f"Alertas -> creadas: {resumen['creadas']}, enviadas: {resumen['enviadas']}, vencidos: {resumen['vencidas']}"
        ))
