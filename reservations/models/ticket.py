from django.db import models, transaction
from .passenger import Passenger
from ..utils.model_utils import TicketStatus
from .berth import Berth


class Ticket(models.Model):
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE)
    berth = models.ForeignKey(Berth, null=True, blank=True, on_delete=models.SET_NULL)  # FK added
    status = models.CharField(max_length=10, choices=TicketStatus.choices, default=TicketStatus.WAITLIST)
    booking_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.passenger.name} - {self.status} ({self.berth.berth_type if self.berth else 'No Berth'})"

    
    @classmethod
    def book_ticket(cls, passenger):
        """
        Tries to book a ticket based on availability (Confirmed → RAC → Waitlist).
        Ensures constraints: 63 Confirmed, 18 RAC, 10 Waitlist.
        """

        with transaction.atomic():
            confirmed_count = cls.objects.filter(status="CONFIRMED").count()
            rac_count = cls.objects.filter(status="RAC").count()
            waitlist_count = cls.objects.filter(status="WAITLIST").count()

            # Assign CONFIRMED berth if available (Max 63)
            if confirmed_count < 63:
                confirmed_berth = Berth.get_available_berth()
                if confirmed_berth:
                    return cls.assign_berth(confirmed_berth, passenger, status="CONFIRMED")

            # Assign RAC berth if available (Max 18 passengers, 9 RAC berths)
            if rac_count < 18:
                rac_berth = Berth.get_rac_berth()
                if rac_berth:
                    return cls.assign_berth(rac_berth, passenger, status="RAC")

            # Assign WAITLIST if available (Max 10)
            if waitlist_count < 10:
                return cls.objects.create(passenger=passenger, status="WAITLIST")

            return "No tickets available"

    @classmethod
    def assign_berth(cls, berth, passenger, status):
        """
        Assigns a berth to a passenger and marks it as occupied.
        """
        ticket = cls.objects.create(passenger=passenger, berth=berth, status=status)
        berth.is_occupied = True
        berth.save()
        return ticket
    

    @classmethod
    def cancel_ticket(cls, ticket_id):
        """
        Cancels a ticket and upgrades the next RAC and WAITLIST passengers accordingly.
        """
        with transaction.atomic():
            ticket = cls.objects.select_for_update().filter(id=ticket_id).first()
            if not ticket:
                return "Ticket not found"

            # Free the berth
            if ticket.berth:
                ticket.berth.is_occupied = False
                ticket.berth.save()

            ticket.delete()

            # Try to upgrade an RAC passenger to CONFIRMED and then WAITLIST passenger to RAC
            rac_ticket = cls.objects.filter(status="RAC").order_by("id").first()
            if rac_ticket:
                confirmed_berth = Berth.get_available_berth()
                if confirmed_berth:
                    rac_ticket.status = "CONFIRMED"
                    rac_ticket.berth = confirmed_berth
                    confirmed_berth.is_occupied = True
                    rac_ticket.save()
                    confirmed_berth.save()

                waitlist_ticket = cls.objects.filter(status="WAITLIST").order_by("id").first()
                if waitlist_ticket:
                    rac_berth = Berth.get_rac_berth()
                    if rac_berth:
                        waitlist_ticket.status = "RAC"
                        waitlist_ticket.berth = rac_berth
                        rac_berth.is_occupied = True
                        waitlist_ticket.save()
                        rac_berth.save()

            return "Ticket canceled successfully"

