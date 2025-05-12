from django.shortcuts import render, get_object_or_404
from shared.decorators import allowed_users
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile
from django.http import JsonResponse
from django.forms.models import model_to_dict
import json

@allowed_users(allowed_roles=['manager', 'waiter', 'inventory'])
def inventoryPage(request):
    return render(request, "inventory.html")


@allowed_users(allowed_roles=['manager', 'waiter', 'kitchen'])
def orderPage(request):
    return render(request, "orders.html")

@allowed_users(allowed_roles=['manager', 'waiter', 'inventory', 'kitchen'])
def schedulePage(request):
    return render(request, "schedules.html")

#Accounts
@allowed_users(allowed_roles=['manager'])
def accountPage(request):
    users = User.objects.select_related('userprofile').all()
    fields_to_display = ['Id','First_name', 'Last_name', 'Username', 'Email', 'Status']
    groups = Group.objects.all() 
    context = {
        'users': users,
        'fields': fields_to_display,
        'all_groups': groups
    }
    return render(request, "accounts.html", context)
@allowed_users(allowed_roles=['manager', 'waiter', 'inventory', 'kitchen'])
def userPage(request):
    return render(request, "user.html")

class UserCreateView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'account_form.html'
    success_url = reverse_lazy('staff:accounts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_groups'] = Group.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create profile with additional data
        profile = self.object.userprofile
        profile.phone = self.request.POST.get('phone', '')
        profile.address = self.request.POST.get('address', '')
        profile.nationalInsurance = self.request.POST.get('national_insurance', '')
        profile.workingHours = float(self.request.POST.get('workHours', 0) or 0)
        profile.annualLeave = float(self.request.POST.get('annualLeave', 0) or 0)
        profile.wage = float(self.request.POST.get('wage', 0) or 0)
        profile.save()
        
        # Handle group assignments
        group_ids = self.request.POST.getlist('groups')
        if group_ids:
            self.object.groups.set(group_ids)
            
        return response


class UserUpdateView(UpdateView):
    model = User
    form_class = UserChangeForm
    template_name = 'account_form.html'
    success_url = reverse_lazy('staff:accounts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_groups'] = Group.objects.all()
        # Add profile form data
        if hasattr(self.object, 'userprofile'):
            context['profile_form'] = self.object.userprofile
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # Save profile data
        profile = self.object.userprofile
        profile.phone = self.request.POST.get('phone', '')
        profile.address = self.request.POST.get('address', '')
        profile.nationalInsurance = self.request.POST.get('national_insurance', '')
        profile.workingHours = float(self.request.POST.get('workHours', 0) or 0)
        profile.annualLeave = float(self.request.POST.get('annualLeave', 0) or 0)
        profile.wage = float(self.request.POST.get('wage', 0) or 0)
        profile.save()
        
        # Handle group assignments
        group_ids = self.request.POST.getlist('groups')
        if group_ids:
            self.object.groups.set(group_ids)
            
        return response

class UserDeleteView(DeleteView):
    model = User
    template_name = 'account_delete.html'
    success_url = reverse_lazy('accounts')

def update_user_groups(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        group_ids = request.POST.getlist('group_ids[]')
        
        try:
            user = User.objects.get(id=user_id)
            user.groups.set(group_ids)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error'}, status=400)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
<<<<<<< HEAD
    try:
        instance.userprofile.save()
    except User.userprofile.RelatedObjectDoesNotExist:
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=instance)
def userPage(request):
    return render(request, "user.html")



=======
    instance.userprofile.save()
>>>>>>> 02b109099066b07c441d151e4d3b64b05365648c

@allowed_users(allowed_roles=['manager'])
def accountPage(request):
    users = User.objects.select_related('userprofile').all()
    fields_to_display = ['Id','First_name', 'Last_name', 'Username', 'Email', 'Status']
    groups = Group.objects.all() 
    context = {
        'users': users,
        'fields': fields_to_display,
        'all_groups': groups
    }
    return render(request, "accounts.html", context)

def get_user_form(request, pk):
    user = get_object_or_404(User, pk=pk)
    groups = Group.objects.all()
    
    form_html = f"""
    <div class="form-group">
        <div class="row">
            <div class="col-md-12">
                <label class="form-label">Username*</label>
                <input type="text" class="form-control" name="username" value="{user.username}" required>
                <small class="text-muted">Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small>
            </div>
        </div>
    </div>
    <div class="form-group">
        <div class="row">
            <div class="col-md-5">
                <label class="control-label" for="inputFirstName">Role:</label>
                <select class="form-select form-select-sm groups-select" 
                        multiple 
                        aria-label="Select groups"
                        data-user-id="{user.id}"
                        name="groups">
                    {"".join([f'<option value="{group.id}" {"selected" if group in user.groups.all() else ""}>{group.name}</option>' for group in groups])}
                </select>
            </div>
            
            <div class="col-md-7">
                <label class="control-label">National Insurance:</label>
                <input type="text" class="form-control" name="national_insurance" value="{user.userprofile.nationalInsurance if hasattr(user, 'userprofile') else ''}">
            </div>
        </div>
    </div>
    <div class="form-group">
        <div class="row">
            <div class="col-md-6">
                <label class="control-label" for="inputFirstName">First name:</label>
                <input type="text" class="form-control" name="first_name" value="{user.first_name}">
            </div>
            <div class="col-md-6">
                <label class="control-label" for="inputLastName">Last Name:</label>
                <input type="text" class="form-control" name="last_name" value="{user.last_name}">
            </div>
        </div>
    </div>
    <div class="form-group">
        <div class="row">
            <div class="col-md-4">
                <label class="control-label" for="inputFirstName">Phone Number:</label>
                <input type="text" class="form-control" name="phone_number" value="{user.userprofile.phone if hasattr(user, 'userprofile') else ''}">
            </div>
            <div class="col-md-8">
                <label class="control-label" for="inputLastName">Address:</label>
                <input type="text" class="form-control" name="address" value="{user.userprofile.address if hasattr(user, 'userprofile') else ''}">
            </div>
        </div>
    </div>
    <div class="form-group">
        <div class="row">
            <div class="col-md-12">
                <label class="form-label">Email</label>
                <input type="email" class="form-control" name="email" value="{user.email}">
            </div>
        </div>
    </div>
    
    <div class="form-group">
        <div class="row">
            <div class="col-md-4">
                <label class="form-label">Working Hours</label>
                <input type="number" class="form-control" name="workHours" value="{user.userprofile.workingHours if hasattr(user, 'userprofile') else ''}">
            </div>
            <div class="col-md-4">
                <label class="form-label">Annual leave</label>
                <input type="number" class="form-control" name="annualLeave" value="{user.userprofile.annualLeave if hasattr(user, 'userprofile') else ''}">
            </div>
            <div class="col-md-4">
                <label class="form-label">Wage</label>
                <input type="number" class="form-control" name="wage" value="{user.userprofile.wage if hasattr(user, 'userprofile') else ''}">
            </div>
        </div>
    </div>
    <div class="mb-3 form-check">
        <input type="checkbox" class="form-check-input" name="is_active" id="is_active_edit" {"checked" if user.is_active else ""}>
        <label class="form-check-label" for="is_active_edit">Employed</label>
    </div>
    """
    
    return JsonResponse({'form_html': form_html})

def create_user_ajax(request):
    if request.method == 'POST':
        try:
            # Create user
            user = User.objects.create_user(
                username=request.POST.get('username'),
                password=request.POST.get('password1'),
                email=request.POST.get('email'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                is_active=request.POST.get('is_active') == 'on'
            )
            
            # Get the user profile (created by signal)
            profile = user.userprofile
            
            # Update profile fields with form data
            profile.phone = request.POST.get('phone_number', '')
            profile.address = request.POST.get('address', '')
            profile.nationalInsurance = request.POST.get('national_insurance', '')
            
            # Handle numeric fields with proper error checking
            try:
                profile.workingHours = float(request.POST.get('workHours', 0) or 0)
            except (ValueError, TypeError):
                profile.workingHours = 0
                
            try:
                profile.annualLeave = float(request.POST.get('annualLeave', 0) or 0)
            except (ValueError, TypeError):
                profile.annualLeave = 0
                
            try:
                profile.wage = float(request.POST.get('wage', 0) or 0)
            except (ValueError, TypeError):
                profile.wage = 0
            
            profile.save()
            
            # Set user groups if provided
            group_ids = request.POST.getlist('groups[]')
            if group_ids:
                user.groups.set(group_ids)
            
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'is_active': user.is_active
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@allowed_users(allowed_roles=['manager'])
def update_user_ajax(request, pk):
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=pk)
            
            # Update user fields with defaults if not provided
            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.is_active = request.POST.get('is_active', 'off') == 'on'
            user.save()
            
            # Get or create profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Update profile fields
            profile_fields = {
                'phone': request.POST.get('phone_number', profile.phone),
                'address': request.POST.get('address', profile.address),
                'nationalInsurance': request.POST.get('national_insurance', profile.nationalInsurance),
                'workingHours': int(float(request.POST.get('workHours', profile.workingHours or 0))),
                'annualLeave': int(float(request.POST.get('annualLeave', profile.annualLeave or 0))),
                'wage': float(request.POST.get('wage', profile.wage or 0.0))
            }
            
            for field, value in profile_fields.items():
                setattr(profile, field, value)
            profile.save()
            
            # Update groups
            group_ids = request.POST.getlist('groups[]', [])
            if group_ids:
                user.groups.set(group_ids)
            
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'is_active': user.is_active
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)

def delete_user_ajax(request, pk):
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=pk)
            user_id = user.id
            user.delete()
            return JsonResponse({'success': True, 'user_id': user_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

