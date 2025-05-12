from django.urls import path, include
from .views import inventoryPage, orderPage, schedulePage, userPage
# homepage, register, CustomLoginView, CustomLogoutView
urlpatterns = [
    path("inventory/", inventoryPage, name="inventory"),
    path("orders/", orderPage, name="orders"),
    path("schedules/", schedulePage, name="schedules"),
    path("accounts/", schedulePage, name="accounts"),
    path("user/", userPage, name="user-page"),
]
