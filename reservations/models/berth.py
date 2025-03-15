from django.db import models
from ..utils.model_utils import BerthType


class Berth(models.Model):
    berth_type = models.CharField(max_length=15, choices=BerthType.choices)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Berth {self.berth_type} ({'Occupied' if self.is_occupied else 'Available'})"

    @classmethod
    def assign_berth(cls, berth_type="ANY"):
        # Priority order for confirmed tickets (avoid SL, SU initially)
        priority_order = ["LOWER", "MIDDLE", "UPPER", "SIDE_LOWER", "SIDE_UPPER"]

        if berth_type == "ANY":
            for btype in priority_order:
                berth = cls.objects.filter(berth_type=btype, is_occupied=False).first()
                if berth:
                    berth.is_occupied = True
                    berth.save(update_fields=["is_occupied"])
                    return berth
        else:
            berth = cls.objects.filter(berth_type=berth_type, is_occupied=False).first()
            if berth:
                berth.is_occupied = True
                berth.save(update_fields=["is_occupied"])
                return berth
