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
        confirmed_count = cls.objects.filter(status="CONFIRMED").count()
        rac_count = cls.objects.filter(status="RAC").count()
        waitlist_count = cls.objects.filter(status="WAITLIST").count()
        
        if waitlist_count >= 10:
            return "No tickets available"
        
        berth = None
        
        if passenger.age < 5:
            # Child under 5 doesn't get a berth, but ticket is still confirmed if available
            if confirmed_count < 63:
                return cls.objects.create(passenger=passenger, status="CONFIRMED")
            elif rac_count < 18:
                return cls.objects.create(passenger=passenger, status="RAC")
            else:
                return cls.objects.create(passenger=passenger, status="WAITLIST")
        
        # Priority for lower berth
        if confirmed_count < 63:
            if passenger.age > 60 or (passenger.gender == "F" and passenger.has_child):
                berth = Berth.assign_berth("LOWER")
                if not berth:
                    berth = Berth.assign_berth("ANY")
            else:
                berth = Berth.assign_berth("ANY")
            
            return cls.objects.create(passenger=passenger, status="CONFIRMED", berth=berth)
        
        # RAC logic (side-lower berth)
        if rac_count < 18:
            berth = Berth.assign_berth("SIDE_LOWER")
            return cls.objects.create(passenger=passenger, status="RAC", berth=berth)
        
        # Waitlist allocation
        if waitlist_count < 10:
            return cls.objects.create(passenger=passenger, status="WAITLIST")
        
        return "No tickets available"
            

    @classmethod
    def cancel_ticket(cls, ticket_id):
        try:
            ticket = cls.objects.get(id=ticket_id)
            with transaction.atomic():
                # Free up the berth if ticket had one
                if ticket.berth:
                    ticket.berth.is_occupied = False
                    ticket.berth.save(update_fields=["is_occupied"])

                status = ticket.status
                ticket.delete()

                if status == "CONFIRMED":
                    # Upgrade RAC → Confirmed
                    rac_ticket = cls.objects.filter(status="RAC").first()
                    if rac_ticket:
                        # vacate previous RAC berth
                        rac_berth = rac_ticket.berth
                        if rac_berth:
                            rac_berth.is_occupied = False
                            rac_berth.save(update_fields=["is_occupied"])
                        
                        # assign confirmed to RAC
                        berth = Berth.assign_berth("ANY")  # Assign any available berth
                        rac_ticket.status = "CONFIRMED"
                        rac_ticket.berth = berth
                        rac_ticket.save(update_fields=["status", "berth"])

                        # Upgrade Waitlist → RAC
                        waitlist_ticket = cls.objects.filter(status="WAITLIST").first()
                        if waitlist_ticket:
                            rac_berth = Berth.assign_berth("SIDE_LOWER")  # Assign RAC berth
                            waitlist_ticket.status = "RAC"
                            waitlist_ticket.berth = rac_berth
                            waitlist_ticket.save(update_fields=["status", "berth"])

                elif status == "RAC":
                    # Upgrade Waitlist → RAC
                    waitlist_ticket = cls.objects.filter(status="WAITLIST").first()
                    if waitlist_ticket:
                        rac_berth = Berth.assign_berth("SIDE_LOWER")  # Assign freed RAC berth
                        waitlist_ticket.status = "RAC"
                        waitlist_ticket.berth = rac_berth
                        waitlist_ticket.save(update_fields=["status", "berth"])

            return "Ticket cancelled successfully"
        except cls.DoesNotExist:
            return "Ticket not found"

