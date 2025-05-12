from django.contrib.auth.models import User
from django.db import models

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
    
from django.db import models
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('unit', 'Unit'),
    ]

    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='unit')
    description = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def needs_reorder(self):
        return self.quantity <= self.reorder_level