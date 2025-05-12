from django.urls import path, include
from .views import (
    inventoryPage, orderPage, schedulePage, userPage, accountPage, 
    UserCreateView, UserUpdateView, UserDeleteView, update_user_groups,
    get_user_form, create_user_ajax, update_user_ajax, delete_user_ajax
)

urlpatterns = [
    path("inventory/", inventoryPage, name="inventory"),
    path("orders/", orderPage, name="orders"),
    path("schedules/", schedulePage, name="schedules"),
    path("accounts/", accountPage, name="accounts"),
    
    # AJAX endpoints
    path('user/create/', create_user_ajax, name='user_create'),
    path('user/<int:pk>/update/form/', get_user_form, name='user_update_form'),
    path('user/<int:pk>/update/', update_user_ajax, name='user_update'),
    path('user/<int:pk>/delete/', delete_user_ajax, name='user_delete'),
    path('update-user-groups/', update_user_groups, name='update_user_groups'),
    
    path("user/", userPage, name="user-page"),
]