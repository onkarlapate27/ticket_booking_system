from django.db import models
from ..utils.model_utils import BerthType


class Berth(models.Model):
    berth_number = models.IntegerField(unique=True)
    berth_type = models.CharField(max_length=15, choices=BerthType.choices)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Berth {self.berth_number} - {self.berth_type} ({'Occupied' if self.is_occupied else 'Available'})"
    
    @classmethod
    def get_available_berth(cls):
        return cls.objects.filter(is_occupied=False).first()

    @classmethod
    def get_rac_berth(cls):
        """Fetches an available side-lower berth for RAC passengers."""
        return cls.objects.filter(berth_type='Side-Lower', is_occupied=False).first()