from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Table, Reservation
from .forms import ReservationForm

# UC1: View Table Availability
class TableAvailabilityView(View):
    def get(self, request):
        # First update all table statuses based on current reservations
        update_all_table_statuses()
        
        tables = Table.objects.all().order_by('table_number')
        # Provide default date (today) and time slots for initial display
        today = timezone.now().date()
        time_slots = generate_time_slots()
        
        context = {
            'tables': tables,
            'today': today,
            'time_slots': time_slots,
        }
        return render(request, 'customer/table_availability.html', context)
    
    def post(self, request):
        # Handle AJAX request for checking availability
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            date_str = request.POST.get('date')
            time_str = request.POST.get('time')
            party_size = int(request.POST.get('party_size', 1))
            
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                time = datetime.strptime(time_str, '%H:%M').time()
                
                # Get suitable tables based on party size
                suitable_tables = Table.objects.filter(capacity__gte=party_size).order_by('capacity')
                
                available_tables = []
                for table in suitable_tables:
                    if table.is_available(date, time):
                        available_tables.append({
                            'id': table.id,
                            'table_number': table.table_number,
                            'capacity': table.capacity,
                            'location': table.location
                        })
                
                return JsonResponse({'available_tables': available_tables})
                
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        
        # Regular form submission - redirect to reservation page with parameters
        date = request.POST.get('date')
        time = request.POST.get('time')
        party_size = request.POST.get('party_size')
        
        return redirect(f'/customer/make-reservation/?date={date}&time={time}&party_size={party_size}')


# UC2: Make Reservation
class MakeReservationView(View):
    def get(self, request):
        # Get parameters from request
        date = request.GET.get('date', timezone.now().date())
        time = request.GET.get('time', '19:00')
        party_size = request.GET.get('party_size', 2)
        table_id = request.GET.get('table_id')
        
        initial_data = {
            'reservation_date': date,
            'reservation_time': time,
            'party_size': party_size,
        }
        
        # If user is authenticated, pre-populate form with user info
        if request.user.is_authenticated:
            initial_data['customer_name'] = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            initial_data['customer_email'] = request.user.email
        
        # If table_id is provided, pre-select that table
        if table_id:
            table = get_object_or_404(Table, id=table_id)
            initial_data['table'] = table
            form = ReservationForm(initial=initial_data)
        else:
            # Otherwise, filter available tables based on party size and date/time
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date() if isinstance(date, str) else date
                time_obj = datetime.strptime(time, '%H:%M').time() if isinstance(time, str) else time
                
                # Get suitable tables
                suitable_tables = Table.objects.filter(capacity__gte=party_size).order_by('capacity')
                available_tables = [table for table in suitable_tables if table.is_available(date_obj, time_obj)]
                
                form = ReservationForm(initial=initial_data)
                # Limit table choices to available tables
                form.fields['table'].queryset = Table.objects.filter(id__in=[t.id for t in available_tables])
            except Exception as e:
                form = ReservationForm(initial=initial_data)
                messages.error(request, f"Error finding available tables: {str(e)}")
        
        return render(request, 'customer/make_reservation.html', {'form': form})
    
    def post(self, request):
        form = ReservationForm(request.POST)
        
        if form.is_valid():
            reservation = form.save(commit=False)
            
            # Validate that the table is still available
            date = reservation.reservation_date
            time = reservation.reservation_time
            if not reservation.table.is_available(date, time):
                messages.error(request, "Sorry, this table has just been reserved by someone else. Please select another table.")
                return self.get(request)
            
            # Explicitly set the status to confirmed
            reservation.status = 'confirmed'
            
            # Save reservation
            reservation.save()
            
            # Double-check that the table status was updated correctly
            table = reservation.table
            if table.status != 'reserved':
                table.status = 'reserved'
                table.save()
                print(f"Table status had to be manually updated to 'reserved'")
            
            # Store email in session for confirmation page access
            request.session['temp_reservation_email'] = reservation.customer_email
            
            messages.success(request, f"Reservation confirmed! Your confirmation code is {reservation.confirmation_code}")
            return redirect('customer:reservation_confirmation', reservation_id=reservation.id)
        else:
            messages.error(request, "There was an error with your reservation. Please check the form and try again.")
            return render(request, 'customer/make_reservation.html', {'form': form})


class ReservationConfirmationView(View):
    def get(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, id=reservation_id)
        
        # Security check - make sure the reservation email matches session email
        if 'temp_reservation_email' in request.session and request.session['temp_reservation_email'] == reservation.customer_email:
            # Clear the session after successful access
            del request.session['temp_reservation_email']
            return render(request, 'customer/reservation_confirmation.html', {'reservation': reservation})
        else:
            messages.error(request, "You don't have permission to view this reservation or your session has expired.")
            return redirect('customer:table_availability')


class CancelReservationView(View):
    def get(self, request):
        # Show a form to find reservation by confirmation code only
        return render(request, 'customer/cancel_reservation_form.html')
    
    def post(self, request):
        confirmation_code = request.POST.get('confirmation_code')
        
        if not confirmation_code:
            messages.error(request, "Please provide your confirmation code.")
            return render(request, 'customer/cancel_reservation_form.html')
        
        try:
            reservation = Reservation.objects.get(
                confirmation_code=confirmation_code,
                status='confirmed'  # Only confirmed reservations can be canceled
            )
            
            # Store reservation ID in session for verification on confirmation page
            request.session['temp_reservation_id'] = reservation.id
            
            return redirect('customer:confirm_cancellation', reservation_id=reservation.id)
            
        except Reservation.DoesNotExist:
            messages.error(request, "No confirmed reservation found with the provided confirmation code.")
            return render(request, 'customer/cancel_reservation_form.html')


class ConfirmCancellationView(View):
    def get(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, id=reservation_id)
        
        # Security check - make sure the reservation ID matches session ID
        if 'temp_reservation_id' in request.session and request.session['temp_reservation_id'] == reservation.id:
            return render(request, 'customer/confirm_cancellation.html', {'reservation': reservation})
        else:
            messages.error(request, "You don't have permission to cancel this reservation or your session has expired.")
            return redirect('customer:cancel_reservation')
    
    def post(self, request, reservation_id):
        reservation = get_object_or_404(Reservation, id=reservation_id)
        
        # Security check - make sure the reservation ID matches session ID
        if 'temp_reservation_id' in request.session and request.session['temp_reservation_id'] == reservation.id:
            # Update reservation status to canceled
            reservation.status = 'cancelled'
            reservation.save()
            
            # Update table status
            table = reservation.table
            table.update_status_based_on_reservations()
            
            # Clear the session
            del request.session['temp_reservation_id']
            
            messages.success(request, "Your reservation has been successfully canceled.")
            return redirect('customer:cancellation_success')
        else:
            messages.error(request, "You don't have permission to cancel this reservation or your session has expired.")
            return redirect('customer:cancel_reservation')


class CancellationSuccessView(View):
    def get(self, request):
        return render(request, 'customer/cancellation_success.html')


# Helper functions
def generate_time_slots():
    """Generate time slots for reservations from restaurant opening to closing times"""
    # These values could come from settings or database
    opening_time = datetime.strptime('11:00', '%H:%M').time()
    closing_time = datetime.strptime('22:00', '%H:%M').time()
    slot_duration = 30  # minutes
    
    slots = []
    current = datetime.combine(datetime.today(), opening_time)
    end = datetime.combine(datetime.today(), closing_time)
    
    while current < end:
        slots.append(current.time())
        current += timedelta(minutes=slot_duration)
    
    return slots


def update_all_table_statuses():
    """
    Update all table statuses based on their current reservations
    """
    tables = Table.objects.all()
    for table in tables:
        table.update_status_based_on_reservations()