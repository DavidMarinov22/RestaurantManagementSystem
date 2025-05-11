from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Reservation, Table

class ReservationForm(forms.ModelForm):
    """Form for customers to make reservations"""
    
    # Add a field for confirming reservation
    confirm_reservation = forms.BooleanField(
        required=True,
        label='I confirm that all the information provided is correct.'
    )
    
    class Meta:
        model = Reservation
        fields = [
            'table', 'customer_name', 'customer_email', 'customer_phone',
            'party_size', 'reservation_date', 'reservation_time'
        ]
        widgets = {
            'reservation_date': forms.DateInput(attrs={'type': 'date'}),
            'reservation_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set minimum date to today
        today = timezone.now().date()
        self.fields['reservation_date'].widget.attrs['min'] = today.strftime('%Y-%m-%d')
        
        # Set maximum date to 30 days from today (or based on restaurant settings)
        max_date = today + timedelta(days=30)
        self.fields['reservation_date'].widget.attrs['max'] = max_date.strftime('%Y-%m-%d')
        
        # Apply Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'confirm_reservation':
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Get form data
        table = cleaned_data.get('table')
        date = cleaned_data.get('reservation_date')
        time = cleaned_data.get('reservation_time')
        party_size = cleaned_data.get('party_size')
        
        # Validate party size against table capacity
        if table and party_size:
            if party_size > table.capacity:
                self.add_error('party_size', f"This table only accommodates up to {table.capacity} guests.")
        
        # Ensure reservation is in the future
        if date and time:
            # Create a naive datetime object (without timezone)
            reservation_datetime = datetime.combine(date, time)
            
            # Get current time as a naive datetime for comparison
            now = timezone.now().replace(tzinfo=None)
            
            if reservation_datetime < now:
                self.add_error('reservation_date', "Reservation must be in the future.")
        
        # Ensure table is available
        if table and date and time:
            if not table.is_available(date, time):
                self.add_error('table', "This table is not available at the selected time.")
        
        return cleaned_data