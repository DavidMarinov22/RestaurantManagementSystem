from django.shortcuts import render, get_object_or_404, redirect
from shared.decorators import allowed_users
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile, MenuItem, Order, OrderItem
from django.http import JsonResponse
from django.forms.models import model_to_dict
from .models import InventoryItem, Category
from .forms import InventoryItemForm, CategoryForm
from django.contrib import messages
from django.db.models import Q, F
from django.utils import timezone
import json
import datetime
from django.core.validators import MinValueValidator

# Order status choices
ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('in_progress', 'In Progress'),
    ('ready', 'Ready for Pickup'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled')
]

@allowed_users(allowed_roles=['manager', 'waiter', 'inventory'])
def inventoryPage(request):
    query = request.GET.get('q')
    items = InventoryItem.objects.all().order_by('name')
    
    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    low_stock = items.filter(quantity__lte=F('reorder_level'))
    
    context = {
        'items': items,
        'low_stock': low_stock,
        'query': query,
    }
    return render(request, 'inventory/inventory.html', context)

def add_item(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item added successfully!')
            return redirect('staff:inventory_list')
    else:
        form = InventoryItemForm()
    
    return render(request, 'inventory/add_item.html', {'form': form})

def edit_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated successfully!')
            return redirect('staff:inventory_list')
    else:
        form = InventoryItemForm(instance=item)
    
    return render(request, 'inventory/edit_item.html', {'form': form, 'item': item})

def delete_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect('staff:inventory_list')
    
    return render(request, 'inventory/confirm_delete.html', {'item': item})

def category_list(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'inventory/categories.html', {'categories': categories})

def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('inventory/categories.html')
    else:
        form = CategoryForm()
    
    return render(request, 'inventory/add_category.html', {'form': form})

@allowed_users(allowed_roles=['manager', 'waiter', 'kitchen'])
def orderPage(request):
    """Order page that redirects based on user role"""
    # For kitchen staff, redirect to kitchen dashboard
    if request.user.groups.filter(name='kitchen').exists():
        return kitchenPage(request)
    
    # For waiters, show waiter order view
    # For waiters, only show their own orders
    if request.user.groups.filter(name='waiter').exists():
        pending_orders = Order.objects.filter(
            waiter=request.user,
            status__in=['pending', 'in_progress', 'ready']
        ).order_by('-created_at')
        
        completed_orders = Order.objects.filter(
            waiter=request.user,
            status='completed'
        ).order_by('-updated_at')[:10]  # Show only the 10 most recent completed orders
    
    # For managers, show all orders
    else:
        pending_orders = Order.objects.filter(
            status__in=['pending', 'in_progress', 'ready']
        ).order_by('-created_at')
        
        completed_orders = Order.objects.filter(
            status='completed'
        ).order_by('-updated_at')[:10]
    
    context = {
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
    }
    
    return render(request, 'orders.html', context)

@allowed_users(allowed_roles=['manager', 'kitchen'])
def kitchenPage(request):
    """View for kitchen staff to see and update orders"""
    # Get all orders that are pending or in progress
    pending_orders = Order.objects.filter(status='pending').order_by('created_at')
    in_progress_orders = Order.objects.filter(status='in_progress').order_by('created_at')
    ready_orders = Order.objects.filter(status='ready').order_by('updated_at')
    
    context = {
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'ready_orders': ready_orders,
    }
    
    return render(request, 'kitchen.html', context)

@allowed_users(allowed_roles=['manager', 'waiter'])
def menuPage(request):
    """View to display the menu for waitstaff to create orders"""
    # Get all menu items grouped by category
    categories = MenuItem.objects.values_list('category', flat=True).distinct()
    menu_by_category = {}
    
    for category in categories:
        menu_by_category[category] = MenuItem.objects.filter(
            category=category, 
            is_available=True
        ).order_by('name')
    
    # Get all tables for selection
    tables = list(range(1, 21))  # Assuming tables 1-20
    
    context = {
        'menu_by_category': menu_by_category,
        'tables': tables,
    }
    
    return render(request, 'menu.html', context)

@allowed_users(allowed_roles=['manager', 'waiter'])
def create_order(request):
    """Handle order creation via AJAX"""
    if request.method == 'POST':
        try:
            print("Create order view called") # Debug statement
            data = json.loads(request.body)
            table_number = data.get('table_number')
            special_instructions = data.get('special_instructions', '')
            items = data.get('items', [])

            # Validate data
            if not table_number or not items:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required data'
                }, status=400)
            
            # Create order
            order = Order.objects.create(
                table_number=table_number,
                waiter=request.user,
                special_instructions=special_instructions,
                status='pending'
            )
            
            # Add order items
            for item in items:
                menu_item = get_object_or_404(MenuItem, id=item.get('id'))
                quantity = item.get('quantity', 1)
                notes = item.get('notes', '')
                
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    notes=notes
                )
            
            return JsonResponse({
                'success': True,
                'order_id': order.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)

@allowed_users(allowed_roles=['manager', 'kitchen', 'waiter'])
def update_order_status(request, order_id):
    """Update the status of an order"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, id=order_id)
            
            # Get status from either POST data or JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                new_status = data.get('status')
            else:
                new_status = request.POST.get('status')
            
            # Validate the new status
            valid_statuses = [status[0] for status in ORDER_STATUS_CHOICES]
            if new_status not in valid_statuses:
                if 'application/json' in request.content_type:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid status'
                    }, status=400)
                else:
                    messages.error(request, 'Invalid status')
                    return redirect('staff:kitchen')
            
            # Update the order status
            order.status = new_status
            order.save()
            
            # Check if this is an AJAX request or regular form submission
            if 'application/json' in request.content_type:
                return JsonResponse({
                    'success': True
                })
            else:
                messages.success(request, f'Order #{order.id} status updated successfully')
                return redirect('staff:kitchen')
            
        except Exception as e:
            if 'application/json' in request.content_type:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
            else:
                messages.error(request, f'Error updating order: {str(e)}')
                return redirect('staff:kitchen')
    
    # For GET requests
    return redirect('staff:kitchen')

@allowed_users(allowed_roles=['manager', 'waiter'])
def order_details(request, order_id):
    """View the details of a specific order"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if the user has permission to view this order
    if not request.user.groups.filter(name='manager').exists() and order.waiter != request.user:
        return redirect('staff:orderPage')
    
    context = {
        'order': order,
        'order_items': order.items.all(),
        'total_price': order.total_price(),
    }
    
    return render(request, 'order_details.html', context)

@allowed_users(allowed_roles=['manager', 'waiter', 'inventory', 'kitchen'])
def schedulePage(request):
    return render(request, "schedules.html")

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
    try:
        instance.userprofile.save()
    except User.userprofile.RelatedObjectDoesNotExist:
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=instance)

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
@allowed_users(allowed_roles=['manager', 'waiter'])
def create_order_simple(request):
    """Simple form-based order creation"""
    if request.method == 'POST':
        # Get form data
        table_number = request.POST.get('table_number')
        special_instructions = request.POST.get('special_instructions', '')
        selected_items = request.POST.getlist('menu_items')
        
        if not table_number or not selected_items:
            messages.error(request, 'Please select a table and at least one menu item')
            return redirect('staff:menu')
        
        try:
            # Create order
            order = Order.objects.create(
                table_number=table_number,
                waiter=request.user,
                special_instructions=special_instructions,
                status='pending',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            # Add order items
            for item_id in selected_items:
                menu_item = get_object_or_404(MenuItem, id=item_id)
                quantity = int(request.POST.get(f'quantity_{item_id}', 1))
                notes = request.POST.get(f'notes_{item_id}', '')
                
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    notes=notes
                )
            
            messages.success(request, f'Order #{order.id} created successfully!')
            return redirect('staff:order_details', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            return redirect('staff:menu')
    
    # GET requests should be redirected to the menu page
    return redirect('staff:menu')