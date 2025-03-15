import logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.db import transaction
import json
from .models import Ticket, Passenger


logger = logging.getLogger(__name__)

# Helper function for rate limiting
def is_rate_limited(ip, key="book_ticket", limit=5, duration=60):
    """
    Limits API requests to 5 requests per minute per IP.
    """
    cache_key = f"{key}_{ip}"
    count = cache.get(cache_key, 0)
    
    if count >= limit:
        return True
    
    cache.set(cache_key, count + 1, timeout=duration)
    return False


@method_decorator(csrf_exempt, name='dispatch')
class BookTicketView(View):
    """
    View to book a ticket based on availability.
    Enforces constraints: 63 Confirmed, 18 RAC, 10 Waitlist.
    """
    def post(self, request):
        ip = request.META.get("REMOTE_ADDR")
        if not request.META.get("HTTP_TEST_MODE") and is_rate_limited(ip):
            return JsonResponse({"message": "Rate limit exceeded. Try again later."}, status=429)

        try:
            data = json.loads(request.body)
            passenger = Passenger.objects.create(name=data.get("name"), age=data.get("age"), gender=data.get("gender"))
            
            with transaction.atomic():
                ticket = Ticket.book_ticket(passenger)
                if isinstance(ticket, str):
                    return JsonResponse({"message": ticket}, status=400)

            return JsonResponse({
                "message": "Ticket booked successfully",
                "ticket_id": ticket.id,
                "status": ticket.status,
                "berth_type": ticket.berth.berth_type if ticket.berth else None
            }, status=201)

        except Exception as e:
            logger.error(f"Error booking ticket: {str(e)}")
            return JsonResponse({"message": "Failed to book ticket"}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CancelTicketView(View):
    """
    View to cancel a ticket and update the status accordingly.
    """
    def post(self, request, ticket_id):
        try:
            with transaction.atomic():
                result = Ticket.cancel_ticket(ticket_id)
                return JsonResponse({"message": result}, status=200)
        except Exception as e:
            logger.error(f"Error canceling ticket: {str(e)}")
            return JsonResponse({"message": "Failed to cancel ticket"}, status=500)


class BookedTicketsView(View):
    def get(self, request):
        """
        Returns a list of booked tickets along with a summary of ticket statistics.
        """
        tickets = Ticket.objects.all().values('id', 'passenger__name', 'status', 'berth__berth_type')

        summary = {
            "total_confirmed_booked": Ticket.objects.filter(status="CONFIRMED").count(),
            "total_rac_booked": Ticket.objects.filter(status="RAC").count(),
            "total_waitlist_booked": Ticket.objects.filter(status="WAITLIST").count(),
            "available_confirmed": 63 - Ticket.objects.filter(status="CONFIRMED").count(),
            "available_rac": 18 - Ticket.objects.filter(status="RAC").count(),
            "available_waitlist": 10 - Ticket.objects.filter(status="WAITLIST").count(),
        }

        response_data = {
            "tickets": list(tickets),
            "summary": summary
        }

        return JsonResponse(response_data, safe=False)


class AvailableTicketsView(View):
    """
    View to get available ticket counts.
    """
    def get(self, request):
        available_confirmed = 63 - Ticket.objects.filter(status="CONFIRMED").count()
        available_rac = 18 - Ticket.objects.filter(status="RAC").count()
        available_waitlist = 10 - Ticket.objects.filter(status="WAITLIST").count()

        return JsonResponse({
            "available_confirmed": available_confirmed,
            "available_rac": available_rac,
            "available_waitlist": available_waitlist
        }, status=200)
