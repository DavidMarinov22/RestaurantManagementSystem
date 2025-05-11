from django.db import models
from django.core.validators import MinValueValidator
from datetime import datetime, timedelta, date, time
from django.utils import timezone

# Constants for table status
TABLE_STATUS_CHOICES = [
    ('available', 'Available'),
    ('reserved', 'Reserved'),
    ('occupied', 'Occupied'),
]

class Table(models.Model):
    """
    Model representing restaurant tables
    """
    table_number = models.IntegerField(unique=True)
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=TABLE_STATUS_CHOICES, default='available')
    location = models.CharField(max_length=50, blank=True)  # e.g., "window", "patio", "main floor"

    def __str__(self):
        return f"Table {self.table_number} (Capacity: {self.capacity})"
    
    def is_available(self, date, time, duration=timedelta(hours=2)):
        """
        Check if this table is available at the specified date and time
        """
        # Only check for overlapping reservations
        # We're not checking table.status here because we want to allow
        # tables that are marked as "reserved" to still be available for
        # different dates or times
            
        # Convert time to datetime for easier comparison (using naive datetimes)
        requested_datetime = datetime.combine(date, time)
        requested_end = requested_datetime + duration
        
        # Check for overlapping reservations
        existing_reservations = self.reservation_set.filter(
            reservation_date=date,
            status='confirmed'
        )
        
        for reservation in existing_reservations:
            reservation_datetime = datetime.combine(reservation.reservation_date, reservation.reservation_time)
            reservation_end = reservation_datetime + duration
            
            # Check if there's an overlap
            if (requested_datetime < reservation_end and requested_end > reservation_datetime):
                return False
                
        return True
    
    def update_status_based_on_reservations(self):
        """
        Updates the table status based on current reservations
        """
        # Get the current date and time
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        # Check if there are any current or upcoming reservations for today
        today_reservations = self.reservation_set.filter(
            reservation_date=today,
            status='confirmed'
        ).order_by('reservation_time')
        
        if not today_reservations.exists():
            # No reservations today, table should be available
            if self.status != 'available':
                self.status = 'available'
                self.save()
            return
        
        # Find the next reservation
        next_reservation = None
        for reservation in today_reservations:
            # Add a buffer before the reservation (e.g., 15 minutes)
            buffer_minutes = 15
            reservation_time_with_buffer = (
                datetime.combine(date.min, reservation.reservation_time) - 
                timedelta(minutes=buffer_minutes)
            ).time()
            
            if reservation_time_with_buffer > current_time:
                next_reservation = reservation
                break
        
        if next_reservation:
            # There's an upcoming reservation today
            # If it's within the next 15 minutes, mark as reserved
            reservation_time = next_reservation.reservation_time
            reservation_datetime = datetime.combine(today, reservation_time)
            current_datetime = datetime.combine(today, current_time)
            
            time_until_reservation = (reservation_datetime - current_datetime).total_seconds() / 60
            
            if time_until_reservation <= 15:  # within 15 minutes
                if self.status != 'reserved':
                    self.status = 'reserved'
                    self.save()
            else:
                # The reservation is later today, but not within 15 minutes
                if self.status != 'available':
                    self.status = 'available'
                    self.save()
        else:
            # All of today's reservations have passed
            if self.status != 'available':
                self.status = 'available'
                self.save()


class Reservation(models.Model):
    """
    Model representing table reservations
    """
    RESERVATION_STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show')
    ]
    
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    party_size = models.IntegerField(validators=[MinValueValidator(1)])
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    confirmation_code = models.CharField(max_length=8, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=RESERVATION_STATUS_CHOICES, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensure we can't have multiple confirmed reservations for the same table, date and time
        constraints = [
            models.UniqueConstraint(
                fields=['table', 'reservation_date', 'reservation_time'],
                condition=models.Q(status='confirmed'),
                name='unique_confirmed_reservation'
            )
        ]

    def __str__(self):
        return f"Reservation for {self.customer_name} on {self.reservation_date} at {self.reservation_time}"
    
    def save(self, *args, **kwargs):
        # Generate a confirmation code if not already set
        if not self.confirmation_code:
            import string
            import random
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            while Reservation.objects.filter(confirmation_code=code).exists():
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.confirmation_code = code
        
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Always update the table status after saving a reservation
        if self.status == 'confirmed':
            # For confirmed reservations, mark the table as reserved
            self.table.status = 'reserved'
            self.table.save()
            print(f"Table {self.table.table_number} status set to: {self.table.status}")
        elif self.status in ['cancelled', 'no_show']:
            # For cancelled or no-show reservations, update table status
            self.table.update_status_based_on_reservations()