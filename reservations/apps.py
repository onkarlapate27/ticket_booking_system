from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ReservationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservations'

    def ready(self):
        from .utils.create_berths import create_berths
        post_migrate.connect(create_berths, sender=self)