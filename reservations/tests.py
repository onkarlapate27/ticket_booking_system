from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from .models import Ticket

class TicketBookingTests(TestCase):
    def setUp(self):
        """Clear cache before each test to avoid rate limit issues."""
        cache.clear()
    
    def book_ticket(self, name, age, gender, test_mode=True):
        return self.client.post(reverse('book_ticket'), {"name": name, "age": age, "gender": gender}, content_type='application/json', HTTP_TEST_MODE=test_mode)
    
    def cancel_ticket(self, ticket_id):
        return self.client.post(reverse('cancel_ticket', args=[ticket_id]))
    
    def test_confirmed_tickets_limit(self):
        """Ensure only 63 confirmed tickets can be booked."""
        for i in range(63):
            response = self.book_ticket(f"Passenger {i+1}", 30, "M")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["status"], "CONFIRMED")

        # 64th ticket should go to RAC
        response = self.book_ticket("RAC Passenger", 30, "M")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "RAC")
    
    def test_rac_tickets_limit(self):
        """Ensure only 18 RAC tickets can be booked before going to waitlist."""
        for i in range(63):
            self.book_ticket(f"Passenger {i+1}", 30, "M")
        for i in range(18):
            response = self.book_ticket(f"RAC Passenger {i+1}", 30, "M")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["status"], "RAC")
        
        # 19th RAC ticket should go to Waitlist
        response = self.book_ticket("Waitlist Passenger", 30, "M")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "WAITLIST")
    
    def test_waitlist_limit(self):
        """Ensure only 10 waitlist tickets can be booked."""
        for i in range(63):
            self.book_ticket(f"Passenger {i+1}", 30, "M")
        for i in range(18):
            self.book_ticket(f"RAC Passenger {i+1}", 30, "M")
        for i in range(10):
            response = self.book_ticket(f"Waitlist Passenger {i+1}", 30, "M")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["status"], "WAITLIST")
        
        # 11th waitlist ticket should be rejected
        response = self.book_ticket("Extra Passenger", 30, "M")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "No tickets available")
    
    def test_lower_berth_priority(self):
        """Ensure lower berths are assigned to seniors and ladies with children."""
        response = self.book_ticket("Senior Passenger", 65, "M")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "CONFIRMED")
        self.assertEqual(response.json()["berth_type"], "LOWER")
    
    def test_rac_allocation_to_side_lower(self):
        """Ensure RAC passengers are assigned side-lower berths."""
        for i in range(63):
            self.book_ticket(f"Passenger {i+1}", 30, "M")
        response = self.book_ticket("RAC Passenger", 30, "M")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "RAC")
        self.assertEqual(response.json()["berth_type"], "SIDE_LOWER")
    
    def test_children_under_5_no_berth(self):
        """Ensure children under 5 are stored but do not get a berth assigned."""
        response = self.book_ticket("Child Passenger", 3, "M")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "CONFIRMED")
        self.assertEqual(response.json()["berth_type"], None)
    
    def test_cancel_ticket_upgrades_rac(self):
        """Ensure that canceling a confirmed ticket upgrades an RAC passenger."""
        for i in range(63):
            self.book_ticket(f"Passenger {i+1}", 30, "M")
        rac_response = self.book_ticket("RAC Passenger", 30, "M")
        rac_ticket_id = rac_response.json()["ticket_id"]
        
        # Cancel a confirmed ticket
        confirmed_ticket = Ticket.objects.filter(status="CONFIRMED").first()
        self.cancel_ticket(confirmed_ticket.id)
        
        # Check if RAC passenger moved to CONFIRMED
        updated_ticket = Ticket.objects.get(id=rac_ticket_id)
        self.assertEqual(updated_ticket.status, "CONFIRMED")
    
    def test_cancel_rac_upgrades_waitlist(self):
        """Ensure that canceling an RAC ticket upgrades a waitlist passenger to RAC."""
        for i in range(63):
            self.book_ticket(f"Passenger {i+1}", 30, "M")
        for i in range(18):
            self.book_ticket(f"RAC Passenger {i+1}", 30, "M")
        waitlist_response = self.book_ticket("Waitlist Passenger", 30, "M")
        waitlist_ticket_id = waitlist_response.json()["ticket_id"]
        
        # Cancel an RAC ticket
        rac_ticket = Ticket.objects.filter(status="RAC").first()
        self.cancel_ticket(rac_ticket.id)

        # Check if waitlist passenger moved to RAC
        updated_ticket = Ticket.objects.get(id=waitlist_ticket_id)
        self.assertEqual(updated_ticket.status, "RAC")
        self.assertEqual(updated_ticket.berth.berth_type, "SIDE_LOWER")

    def test_cancel_confirmed_upgrades_rac_and_waitlist(self):
        """Ensure that canceling a confirmed ticket upgrades an RAC passenger to confirmed
        and a waitlist passenger to RAC.
        """
        # Fill Confirmed, RAC, and Waitlist limits
        for i in range(63):
            self.book_ticket(f"Confirmed Passenger {i+1}", 30, "M")
        for i in range(18):
            self.book_ticket(f"RAC Passenger {i+1}", 30, "M")
        waitlist_response = self.book_ticket("Waitlist Passenger", 30, "M")
        waitlist_ticket_id = waitlist_response.json()["ticket_id"]

        # Get the first RAC ticket
        rac_ticket = Ticket.objects.filter(status="RAC").first()
        rac_ticket_id = rac_ticket.id

        # Cancel a Confirmed ticket
        confirmed_ticket = Ticket.objects.filter(status="CONFIRMED").first()
        self.cancel_ticket(confirmed_ticket.id)

        # Check if RAC passenger moved to Confirmed
        updated_rac_ticket = Ticket.objects.get(id=rac_ticket_id)
        self.assertEqual(updated_rac_ticket.status, "CONFIRMED")
        self.assertIsNotNone(updated_rac_ticket.berth)  # Should have a confirmed berth

        # Check if Waitlist passenger moved to RAC
        updated_waitlist_ticket = Ticket.objects.get(id=waitlist_ticket_id)
        self.assertEqual(updated_waitlist_ticket.status, "RAC")
        self.assertEqual(updated_waitlist_ticket.berth.berth_type, "SIDE_LOWER")

    def test_rate_limit(self):
        """Ensure that more than 5 requests per minute are blocked."""
        for _ in range(5):
            response = self.book_ticket("Rate Limit Test", 30, "M", test_mode=False)
            self.assertIn(response.status_code, [201, 400])
        response = self.book_ticket("Rate Limit Exceeded", 30, "M", test_mode=False)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["message"], "Rate limit exceeded. Try again later.")