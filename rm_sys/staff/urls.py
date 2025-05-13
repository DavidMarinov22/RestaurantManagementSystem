from django.urls import path, include
from .views import (
    inventoryPage, orderPage, schedulePage, userPage, accountPage,
    UserCreateView, UserUpdateView, UserDeleteView, update_user_groups,
    get_user_form, create_user_ajax, update_user_ajax, delete_user_ajax,
    add_item, edit_item, delete_item, category_list, add_category,
    # New order management views
    menuPage, create_order, kitchenPage, update_order_status, order_details,create_order_simple
)

urlpatterns = [
    path("inventory/", inventoryPage, name="inventory"),
    path("orders/", orderPage, name="orders"),
    path("waiter-orders/", orderPage, name="waiter_orders"),
    path("schedules/", schedulePage, name="schedules"),
    path("accounts/", accountPage, name="accounts"),
    path("user/", userPage, name="user-page"),
    # Add this to your urlpatterns
    path("create_order_simple/", create_order_simple, name="create_order_simple"),  
    
    # Inventory
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
    
    # Orders
    path("menu/", menuPage, name="menu"),
    path("create_order/", create_order, name="create_order"),
    path("kitchen/", kitchenPage, name="kitchen"),
    path("update_order/<int:order_id>/", update_order_status, name="update_order_status"),
    path("order_details/<int:order_id>/", order_details, name="order_details"),
]