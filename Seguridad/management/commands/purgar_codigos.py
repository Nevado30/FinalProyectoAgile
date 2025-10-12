from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from Seguridad.models import EmailVerification

class Command(BaseCommand):
    help = "Elimina verificaciones viejas (usadas o vencidas de hace > 1 día)."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=1)
        qs = EmailVerification.objects.filter(created_at__lt=cutoff)
        n = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Eliminadas {n} verificaciones antiguas"))
