from django.apps import AppConfig

class PrestamosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Prestamos'

    def ready(self):
        import Prestamos.signals  # noqa
