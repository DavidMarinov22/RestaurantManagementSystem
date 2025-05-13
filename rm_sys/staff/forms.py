from django import forms
from .models import (
    InventoryItem, Category, Schedule, ScheduleChangeRequest,
    SCHEDULE_STATUS_CHOICES, REQUEST_TYPE_CHOICES
)
import datetime

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['staff', 'start_time', 'end_time', 'note', 'status']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        # Check if end time is after start time
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError("End time must be after start time")
            
        return cleaned_data

class ScheduleChangeRequestForm(forms.ModelForm):
    class Meta:
        model = ScheduleChangeRequest
        fields = ['original_schedule', 'requested_start_time', 'requested_end_time', 'request_type', 'reason']
        widgets = {
            'requested_start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'requested_end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, user=None, *args, **kwargs):
        super(ScheduleChangeRequestForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['original_schedule'].queryset = Schedule.objects.filter(staff=user)
            # For staff, the original_schedule is required for change requests but not for time off
            self.fields['original_schedule'].required = False
            self.fields['original_schedule'].label = "Original Schedule (required for change requests)"

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('requested_start_time')
        end_time = cleaned_data.get('requested_end_time')
        request_type = cleaned_data.get('request_type')
        original_schedule = cleaned_data.get('original_schedule')

        # Check if end time is after start time
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError("End time must be after start time")
        
        # If request type is 'change', original schedule should be provided
        if request_type == 'change' and not original_schedule:
            raise forms.ValidationError("For change requests, an original schedule must be selected")
            
        return cleaned_data

class ScheduleChangeReviewForm(forms.ModelForm):
    class Meta:
        model = ScheduleChangeRequest
        fields = ['status', 'manager_note']
        widgets = {
            'manager_note': forms.Textarea(attrs={'rows': 3}),
        }