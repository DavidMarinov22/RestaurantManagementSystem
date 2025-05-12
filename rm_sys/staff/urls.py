from django.urls import path, include
from .views import (
    inventoryPage, orderPage, schedulePage, userPage, accountPage, 
    UserCreateView, UserUpdateView, UserDeleteView, update_user_groups,
    get_user_form, create_user_ajax, update_user_ajax, delete_user_ajax,
    inventoryPage, add_item, edit_item, delete_item, category_list, add_category
)

urlpatterns = [
    path("inventory/", inventoryPage, name="inventory"),
    path("orders/", orderPage, name="orders"),
    path("schedules/", schedulePage, name="schedules"),
    path("accounts/", accountPage, name="accounts"),
    path("user/", userPage, name="user-page"),
    
    #Inventory
    path('inventory/', inventoryPage, name='inventory_list'),
    path('inventory/add/', add_item, name='add_item'),
    path('inventory/edit/<int:item_id>/', edit_item, name='edit_item'),
    path('inventory/delete/<int:item_id>/', delete_item, name='delete_item'),
    path('inventory/categories/', category_list, name='category_list'),
    path('inventory/categories/add/', add_category, name='add_category'),

    # Accounts
    path('user/create/', create_user_ajax, name='user_create'),
    path('user/<int:pk>/update/form/', get_user_form, name='user_update_form'),
    path('user/<int:pk>/update/', update_user_ajax, name='user_update'),
    path('user/<int:pk>/delete/', delete_user_ajax, name='user_delete'),
    path('update-user-groups/', update_user_groups, name='update_user_groups'),
    
]