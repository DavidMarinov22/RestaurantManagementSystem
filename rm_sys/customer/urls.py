from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    # UC1: View Table Availability
    path('tables/', views.TableAvailabilityView.as_view(), name='table_availability'),
    
    # UC2: Make Reservation
    path('make-reservation/', views.MakeReservationView.as_view(), name='make_reservation'),
    path('reservation-confirmation/<int:reservation_id>/', views.ReservationConfirmationView.as_view(), name='reservation_confirmation'),
    
    # Cancel Reservation
    path('cancel-reservation/', views.CancelReservationView.as_view(), name='cancel_reservation'),
    path('confirm-cancellation/<int:reservation_id>/', views.ConfirmCancellationView.as_view(), name='confirm_cancellation'),
    path('cancellation-success/', views.CancellationSuccessView.as_view(), name='cancellation_success'),
]