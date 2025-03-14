from django.db import models


class BerthType(models.TextChoices):
    LOWER = 'LOWER', 'Lower'
    MIDDLE = 'MIDDLE', 'Middle'
    UPPER = 'UPPER', 'Upper'
    SIDE_LOWER = 'SIDE_LOWER', 'Side Lower'
    SIDE_UPPER = 'SIDE_UPPER', 'Side Upper'


class TicketStatus(models.TextChoices):
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    RAC = 'RAC', 'RAC'
    WAITLIST = 'WAITLIST', 'Waitlist'