"""
URL configuration for rm_sys project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path , include
from customer.views import CustomerMenuView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include(('shared.urls', "shared"), "shared")),
    path('', include(('customer.urls', 'customer'), 'customer')),
    path('', include(('staff.urls', "staff"), "staff")),
    path('customer/menu/', CustomerMenuView.as_view(), name='customer_menu'),
]
