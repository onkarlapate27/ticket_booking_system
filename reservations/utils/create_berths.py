from django.db.models.signals import post_migrate
from django.dispatch import receiver
from ..models.berth import Berth
from .model_utils import BerthType


@receiver(post_migrate)
def create_berths(sender, **kwargs):
    if not Berth.objects.exists():
        berth_distribution = {
            BerthType.LOWER: 21,
            BerthType.MIDDLE: 21,
            BerthType.UPPER: 21,
            BerthType.SIDE_LOWER: 9,
            BerthType.SIDE_UPPER: 9,
        }

        berths = [
            Berth(berth_type=berth_type, is_occupied=False)
            for berth_type, count in berth_distribution.items()
            for _ in range(count)
        ]
        Berth.objects.bulk_create(berths)

        print("Berths created automatically after migration!")