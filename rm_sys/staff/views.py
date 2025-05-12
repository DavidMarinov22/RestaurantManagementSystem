from django.shortcuts import render
from shared.decorators import allowed_users

@allowed_users(allowed_roles=['manager', 'waiter', 'inventory'])
def inventoryPage(request):
    return render(request, "inventory.html")

@allowed_users(allowed_roles=['manager'])
def accountPage(request):
    return render(request, "accounts.html")

@allowed_users(allowed_roles=['manager', 'waiter', 'kitchen'])
def orderPage(request):
    return render(request, "orders.html")

@allowed_users(allowed_roles=['manager', 'waiter', 'inventory', 'kitchen'])
def schedulePage(request):
    return render(request, "schedules.html")

def userPage(request):
    return render(request, "user.html")
