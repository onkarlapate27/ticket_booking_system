from django.urls import path
from .views import BookTicketView, CancelTicketView, BookedTicketsView, AvailableTicketsView

urlpatterns = [
    path('api/v1/tickets/book', BookTicketView.as_view(), name='book_ticket'),
    path('api/v1/tickets/cancel/<int:ticket_id>', CancelTicketView.as_view(), name='cancel_ticket'),
    path('api/v1/tickets/booked', BookedTicketsView.as_view(), name='booked_tickets'),
    path('api/v1/tickets/available', AvailableTicketsView.as_view(), name='available_tickets'),
]
