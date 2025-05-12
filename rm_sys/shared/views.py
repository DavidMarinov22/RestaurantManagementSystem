from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages 
from .decorators import unauthenticated_user, allowed_users

def homepage(request):
    return render(request , "homepage.html", {})


@unauthenticated_user
@allowed_users(allowed_roles=['manager'])
def registerPage(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect("shared:login")
    else:
        form = UserCreationForm()
    context = {"form" :form}
    return render(request, "registration/register.html", context)

@unauthenticated_user
def loginPage(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)    
            return redirect('staff:user-page')
        else:
            messages.info(request, "Username OR password is incorrect")

    context = {}
    return render(request, "registration/login.html", context)

def logoutUser(request):
    logout(request)
    return redirect("shared:login")


