from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import datetime, timedelta, date, time

# Order status choices
ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('ready', 'Ready for Pickup'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled')
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    role = models.CharField(max_length=100, blank=True)
    workingHours = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    nationalInsurance = models.CharField(max_length=100, blank=True)
    annualLeave = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    wage = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    """Model representing items on the menu"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.CharField(max_length=50)  # e.g., 'Appetizer', 'Main Course', 'Dessert'
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
class Order(models.Model):
    """Model representing a customer order"""
    table_number = models.IntegerField(validators=[MinValueValidator(1)])
    waiter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - Table {self.table_number}"
    
    def total_price(self):
        """Calculate the total price of the order"""
        return sum(item.quantity * item.menu_item.price for item in self.items.all())

class OrderItem(models.Model):
    """Model representing items within an order"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"
    
    def item_total(self):
        """Calculate the total price for this line item"""
        return self.quantity * self.menu_item.price