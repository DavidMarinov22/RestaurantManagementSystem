from django.urls import path
from .views import (
    TableAvailabilityView,
    MakeReservationView,
    ReservationConfirmationView,
    CancelReservationView,
    ConfirmCancellationView,
    CancellationSuccessView,
    CustomerMenuView
)

app_name = 'customer'

urlpatterns = [
    # UC1: View Table Availability
    path('tables/', TableAvailabilityView.as_view(), name='table_availability'),
    
    # UC2: Make Reservation
    path('make-reservation/', MakeReservationView.as_view(), name='make_reservation'),
    path('reservation-confirmation/<int:reservation_id>/', ReservationConfirmationView.as_view(), name='reservation_confirmation'),
    
    # Cancel Reservation
    path('cancel-reservation/', CancelReservationView.as_view(), name='cancel_reservation'),
    path('confirm-cancellation/<int:reservation_id>/', ConfirmCancellationView.as_view(), name='confirm_cancellation'),
    path('cancellation-success/', CancellationSuccessView.as_view(), name='cancellation_success'),
    
    # Menu View
    path('menu/', CustomerMenuView.as_view(), name='menu'),
]